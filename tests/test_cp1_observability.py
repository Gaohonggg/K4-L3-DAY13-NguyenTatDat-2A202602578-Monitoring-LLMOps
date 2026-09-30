from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import httpx

from app import logging_config
from app import main as main_module
from app.main import app
from app.pii import hash_user_id


def test_concurrent_requests_keep_separate_context_and_response_headers(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    async def send_requests() -> tuple[httpx.Response, httpx.Response]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await asyncio.gather(
                client.post(
                    "/chat",
                    headers={"x-request-id": "req-ABCDEF01"},
                    json={
                        "user_id": "student-a",
                        "session_id": "session-a",
                        "feature": "qa",
                        "message": "Explain monitoring",
                    },
                ),
                client.post(
                    "/chat",
                    headers={"x-request-id": "invalid-id"},
                    json={
                        "user_id": "student-b",
                        "session_id": "student@example.invalid",
                        "feature": "summary",
                        "message": "Call 0901234567 about CCCD 012345678901 and card 4111 1111 1111 1111",
                    },
                ),
            )

    supplied, generated = asyncio.run(send_requests())

    assert supplied.status_code == generated.status_code == 200
    assert supplied.headers["x-request-id"] == "req-abcdef01"
    assert re.fullmatch(r"req-[0-9a-f]{8}", generated.headers["x-request-id"])
    assert generated.headers["x-request-id"] != supplied.headers["x-request-id"]
    for response in (supplied, generated):
        assert response.json()["correlation_id"] == response.headers["x-request-id"]
        assert float(response.headers["x-response-time-ms"]) >= 0

    raw_logs = log_path.read_text(encoding="utf-8")
    for raw_pii in (
        "student@example.invalid",
        "0901234567",
        "012345678901",
        "4111 1111 1111 1111",
    ):
        assert raw_pii not in raw_logs

    events = [json.loads(line) for line in raw_logs.splitlines()]
    received = {
        event["correlation_id"]: event
        for event in events
        if event["event"] == "request_received"
    }
    sent = {
        event["correlation_id"]: event
        for event in events
        if event["event"] == "response_sent"
    }
    assert set(received) == set(sent) == {
        supplied.headers["x-request-id"],
        generated.headers["x-request-id"],
    }
    assert received["req-abcdef01"]["user_id_hash"] == hash_user_id("student-a")
    assert received["req-abcdef01"]["session_id"] == "session-a"
    generated_log = received[generated.headers["x-request-id"]]
    assert generated_log["user_id_hash"] == hash_user_id("student-b")
    assert generated_log["session_id"] == "[REDACTED_EMAIL]"
    assert generated_log["feature"] == "summary"
    assert generated_log["model"] == "claude-sonnet-4-5"
    assert generated_log["env"] == "dev"


def test_failed_request_retains_id_and_scrubs_exception_detail(
    monkeypatch, tmp_path: Path
) -> None:
    log_path = tmp_path / "logs.jsonl"
    monkeypatch.setattr(logging_config, "LOG_PATH", log_path)

    def fail(**_: str) -> None:
        raise RuntimeError("Timeout for student@example.invalid")

    monkeypatch.setattr(main_module.agent, "run", fail)

    async def send_request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.post(
                "/chat",
                headers={"x-request-id": "req-deadbeef"},
                json={
                    "user_id": "student-error",
                    "session_id": "session-error",
                    "feature": "qa",
                    "message": "Explain monitoring",
                },
            )

    response = asyncio.run(send_request())

    assert response.status_code == 500
    assert response.headers["x-request-id"] == "req-deadbeef"
    raw_logs = log_path.read_text(encoding="utf-8")
    assert "student@example.invalid" not in raw_logs
    failed = next(
        json.loads(line)
        for line in raw_logs.splitlines()
        if json.loads(line)["event"] == "request_failed"
    )
    assert failed["correlation_id"] == "req-deadbeef"
    assert failed["payload"]["detail"] == "Timeout for [REDACTED_EMAIL]"
