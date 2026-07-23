from __future__ import annotations
from typing import Any


def build_team_execution_package(objective: str, country: str = "Kazakhstan", industries: list | None = None, evidence: list | None = None, audience: str = "internal") -> dict[str, Any]:
    return {
        "ok": True,
        "objective": objective,
        "country": country,
        "industries": industries or ["infrastructure", "mining", "logistics", "energy"],
        "package": {
            "context_brief": f"Execution package for: {objective}",
            "action_items": [
                {"task": "research_market", "assignee": "analyst", "status": "pending"},
                {"task": "identify_partners", "assignee": "business_dev", "status": "pending"},
                {"task": "risk_assessment", "assignee": "risk_team", "status": "pending"},
            ],
            "timeline": "2_weeks",
            "resources_required": ["market_data", "partner_database", "risk_models"],
        },
        "evidence_count": len(evidence or []),
        "audience": audience,
    }
