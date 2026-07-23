from __future__ import annotations
from typing import Any


def build_and_write_action_board(case: dict[str, Any], evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    project = case.get("project", "Unknown")
    return {
        "ok": True,
        "project": project,
        "case": case,
        "evidence_summary": evidence,
        "actions": [
            {"action": "gather_evidence", "status": "pending", "priority": "high"},
            {"action": "risk_assessment", "status": "pending", "priority": "medium"},
            {"action": "stakeholder_review", "status": "pending", "priority": "medium"},
        ],
        "board_status": "active",
    }
