from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

import yaml

from .metrics import percentile


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "dashboard.yaml"


def _load_records(log_path: Path, window_start: datetime, now: datetime) -> list[dict[str, Any]]:
    if not log_path.exists():
        return []

    records: list[dict[str, Any]] = []
    with log_path.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    continue
                timestamp = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
            except (ValueError, KeyError, TypeError):
                continue
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            if (
                record.get("service") == "api"
                and record.get("event") in {"request_received", "response_sent", "request_failed"}
                and window_start <= timestamp <= now
            ):
                record["_timestamp"] = timestamp
                records.append(record)
    return records


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(100 * numerator / denominator, 2) if denominator else None


def build_dashboard_snapshot(log_path: Path, now: datetime | None = None) -> dict[str, Any]:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))["dashboard"]
    now = now or datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=config["time_range_minutes"])
    records = _load_records(log_path, window_start, now)
    panels = {panel["id"]: panel for panel in config["panels"]}

    received = [record for record in records if record["event"] == "request_received"]
    sent = [record for record in records if record["event"] == "response_sent"]
    failed = [record for record in records if record["event"] == "request_failed"]
    retrieval_events = [
        record
        for record in (*sent, *failed)
        if record.get("tool_name") == "retrieval" and record.get("tool_success") is not None
    ]
    latencies = [int(record["latency_ms"]) for record in sent if record.get("latency_ms") is not None]
    ttfts = [int(record["ttft_ms"]) for record in sent if record.get("ttft_ms") is not None]
    costs = [float(record.get("cost_usd") or 0) for record in sent]
    qualities = [float(record["quality_score"]) for record in sent if record.get("quality_score") is not None]

    by_minute: dict[datetime, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_minute[record["_timestamp"].replace(second=0, microsecond=0)].append(record)
    minutes = [
        window_start.replace(second=0, microsecond=0) + timedelta(minutes=offset)
        for offset in range(config["time_range_minutes"] + 1)
    ]
    series: list[dict[str, Any]] = []
    for minute in minutes:
        bucket = by_minute[minute]
        bucket_sent = [record for record in bucket if record["event"] == "response_sent"]
        bucket_latencies = [
            int(record["latency_ms"])
            for record in bucket_sent
            if record.get("latency_ms") is not None
        ]
        bucket_qualities = [
            float(record["quality_score"])
            for record in bucket_sent
            if record.get("quality_score") is not None
        ]
        series.append(
            {
                "minute": minute.strftime("%H:%M"),
                "traffic": sum(record["event"] == "request_received" for record in bucket),
                "errors": sum(record["event"] == "request_failed" for record in bucket),
                "latency_p95": percentile(bucket_latencies, 95) if bucket_latencies else None,
                "cost_usd": round(sum(float(record.get("cost_usd") or 0) for record in bucket_sent), 6),
                "tokens_in": sum(int(record.get("tokens_in") or 0) for record in bucket_sent),
                "tokens_out": sum(int(record.get("tokens_out") or 0) for record in bucket_sent),
                "tokens_total": sum(
                    int(record.get("tokens_in") or 0) + int(record.get("tokens_out") or 0)
                    for record in bucket_sent
                ),
                "quality_avg": round(mean(bucket_qualities), 3) if bucket_qualities else None,
            }
        )

    return {
        "generated_at": now.isoformat(),
        "window_start": window_start.isoformat(),
        "time_range_minutes": config["time_range_minutes"],
        "refresh_seconds": config["refresh_seconds"],
        "panels": {
            "latency": {
                "title": panels["latency"]["title"],
                "unit": panels["latency"]["unit"],
                "threshold": panels["latency"]["threshold"]["value"],
                "p50": percentile(latencies, 50) if latencies else None,
                "p95": percentile(latencies, 95) if latencies else None,
                "p99": percentile(latencies, 99) if latencies else None,
                "ttft_p95": percentile(ttfts, 95) if ttfts else None,
            },
            "traffic": {
                "title": panels["traffic"]["title"],
                "unit": panels["traffic"]["unit"],
                "threshold": panels["traffic"]["threshold"]["value"],
                "count": len(received),
                "rate_per_minute": sum(
                    record["_timestamp"] >= now - timedelta(minutes=1) for record in received
                ),
            },
            "errors": {
                "title": panels["errors"]["title"],
                "unit": panels["errors"]["unit"],
                "threshold": panels["errors"]["threshold"]["value"],
                "error_rate_pct": _ratio(len(failed), len(received)),
                "error_count": len(failed),
                "breakdown": dict(Counter(record.get("error_type") or "unknown" for record in failed)),
                "retrieval_success_rate_pct": _ratio(
                    sum(record["tool_success"] is True for record in retrieval_events),
                    len(retrieval_events),
                ),
            },
            "cost": {
                "title": panels["cost"]["title"],
                "unit": panels["cost"]["unit"],
                "threshold": panels["cost"]["threshold"]["value"],
                "total": round(sum(costs), 6),
            },
            "tokens": {
                "title": panels["tokens"]["title"],
                "unit": panels["tokens"]["unit"],
                "threshold": panels["tokens"]["threshold"]["value"],
                "input_total": sum(int(record.get("tokens_in") or 0) for record in sent),
                "output_total": sum(int(record.get("tokens_out") or 0) for record in sent),
            },
            "quality": {
                "title": panels["quality"]["title"],
                "unit": panels["quality"]["unit"],
                "threshold": panels["quality"]["threshold"]["value"],
                "mean": round(mean(qualities), 3) if qualities else None,
            },
        },
        "series": series,
    }
