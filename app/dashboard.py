from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from . import logging_config
from .dashboard_metrics import build_dashboard_snapshot


router = APIRouter()
HTML_PATH = Path(__file__).resolve().parent / "static" / "dashboard.html"


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard() -> HTMLResponse:
    return HTMLResponse(HTML_PATH.read_text(encoding="utf-8"))


@router.get("/dashboard/data")
def dashboard_data() -> dict:
    return build_dashboard_snapshot(logging_config.LOG_PATH)
