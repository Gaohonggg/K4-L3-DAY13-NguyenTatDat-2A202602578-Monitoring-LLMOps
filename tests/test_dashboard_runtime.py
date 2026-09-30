from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

from app import logging_config
from app.dashboard_metrics import build_dashboard_snapshot
from app.main import app


def _record(now: datetime, event: str, **fields: object) -> dict:
    return {
        "ts": (now - timedelta(seconds=10)).isoformat(),
        "service": "api",
        "event": event,
        **fields,
    }


def test_dashboard_aggregates_six_panels_from_jsonl(tmp_path: Path) -> None:
    now = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)
    records = [
        _record(now, "request_received"),
        _record(now, "request_received"),
        _record(now, "request_received"),
        _record(
            now,
            "response_sent",
            latency_ms=100,
            ttft_ms=20,
            cost_usd=0.01,
            tokens_in=10,
            tokens_out=20,
            quality_score=0.8,
            tool_name="retrieval",
            tool_success=True,
        ),
        _record(
            now,
            "response_sent",
            latency_ms=300,
            ttft_ms=40,
            cost_usd=0.02,
            tokens_in=20,
            tokens_out=30,
            quality_score=0.6,
            tool_name="retrieval",
            tool_success=True,
        ),
        _record(
            now,
            "request_failed",
            error_type="RuntimeError",
            tool_name="retrieval",
            tool_success=False,
        ),
        {
            **_record(now, "request_received"),
            "ts": (now - timedelta(hours=2)).isoformat(),
        },
    ]
    log_path = tmp_path / "logs.jsonl"
    log_path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")

    snapshot = build_dashboard_snapshot(log_path, now)
    panels = snapshot["panels"]

    assert set(panels) == {"latency", "traffic", "errors", "cost", "tokens", "quality"}
    assert snapshot["time_range_minutes"] == 60
    assert snapshot["refresh_seconds"] == 30
    assert panels["latency"]["p50"] == 100
    assert panels["latency"]["p95"] == 300
    assert panels["latency"]["ttft_p95"] == 40
    assert panels["traffic"]["count"] == 3
    assert panels["traffic"]["rate_per_minute"] == 3
    assert panels["errors"]["error_rate_pct"] == 33.33
    assert panels["errors"]["retrieval_success_rate_pct"] == 66.67
    assert panels["errors"]["breakdown"] == {"RuntimeError": 1}
    assert panels["cost"]["total"] == 0.03
    assert panels["tokens"]["input_total"] == 30
    assert panels["tokens"]["output_total"] == 50
    assert panels["quality"]["mean"] == 0.7
    assert snapshot["series"][-2]["traffic"] == 3


def test_dashboard_routes_serve_html_and_live_data(monkeypatch, tmp_path: Path) -> None:
    log_path = tmp_path / "logs.jsonl"
    now = datetime.now(timezone.utc)
    log_path.write_text(json.dumps(_record(now, "request_received")), encoding="utf-8")
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    async def get_routes() -> tuple[httpx.Response, httpx.Response]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/dashboard"), await client.get("/dashboard/data")

    page, data = asyncio.run(get_routes())

    assert page.status_code == data.status_code == 200
    assert 'id="latency"' in page.text
    assert 'id="quality"' in page.text
    assert data.json()["panels"]["traffic"]["count"] == 1
