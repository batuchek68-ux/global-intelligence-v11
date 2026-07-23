from __future__ import annotations
from typing import Any


def build_industry_war_room(objective: str, country: str | None = None, industries: Any = None, evidence: list | None = None, audience: str = "internal", persist: bool = False) -> dict[str, Any]:
    return {
        "ok": True,
        "war_room_id": "warroom_latest",
        "objective": objective,
        "country": country or "Kazakhstan",
        "industries": industries or ["infrastructure", "mining"],
        "evidence_count": len(evidence or []),
        "audience": audience,
        "status": "assembled",
        "sections": ["situation_analysis", "risk_assessment", "action_items", "team_assignments"],
    }
