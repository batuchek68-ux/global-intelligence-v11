from __future__ import annotations
from typing import Any
from pathlib import Path


REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"


def read_text_report(relative_path: str) -> dict[str, Any]:
    report_file = REPORTS_DIR / relative_path
    if report_file.exists():
        content = report_file.read_text(encoding="utf-8")
        return {"ok": True, "path": relative_path, "content": content}
    return {"ok": False, "path": relative_path, "content": "", "note": "Report not found."}


def dashboard_summary() -> dict[str, Any]:
    return {
        "ok": True,
        "summary": {
            "active_projects": 0,
            "pending_decisions": 0,
            "completed_tasks": 0,
            "system_health": "operational",
        },
    }
