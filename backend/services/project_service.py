from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json


@dataclass
class Project:
    title: str = ""
    topic: str = ""
    country: str = "Kazakhstan"
    industry: str = "infrastructure"
    status: str = "draft"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict = field(default_factory=dict)


def build_project_intake(body: dict[str, Any]) -> Project:
    return Project(
        title=body.get("title", ""),
        topic=body.get("topic", body.get("query", "")),
        country=body.get("country", "Kazakhstan"),
        industry=body.get("industry", "infrastructure"),
        metadata=body.get("metadata", {}),
    )


def analyze_project(body: dict[str, Any]) -> dict[str, Any]:
    project = body.get("project", body)
    return {
        "ok": True,
        "project": project,
        "analysis": {
            "feasibility": "moderate",
            "risk_level": "medium",
            "estimated_value": "unknown",
            "recommended_actions": ["gather_market_data", "assess_competition", "evaluate_risks"],
        },
    }
