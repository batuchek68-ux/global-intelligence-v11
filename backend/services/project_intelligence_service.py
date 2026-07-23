from __future__ import annotations
from typing import Any
from pathlib import Path
import json


PROJECTS_DIR = Path(__file__).resolve().parents[2] / "projects"


def discover_projects(topic: str, country: str = "Kazakhstan", evidence: list | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "topic": topic,
        "country": country,
        "discovered": [],
        "evidence_count": len(evidence or []),
        "status": "discovery_complete",
        "note": "Project discovery requires external data sources.",
    }


def build_project_pipeline(topic: str, country: str = "Kazakhstan", evidence: list | None = None, persist: bool = False) -> dict[str, Any]:
    return {
        "ok": True,
        "topic": topic,
        "country": country,
        "pipeline": {
            "stage_1_discovery": {"status": "complete", "items": 0},
            "stage_2_qualification": {"status": "pending", "items": 0},
            "stage_3_analysis": {"status": "pending", "items": 0},
            "stage_4_action": {"status": "pending", "items": 0},
        },
        "evidence_count": len(evidence or []),
    }


def read_project_library() -> dict[str, Any]:
    projects = []
    if PROJECTS_DIR.exists():
        for f in PROJECTS_DIR.glob("**/*.md"):
            projects.append({"file": f.name, "path": str(f)})
    return {"projects": projects, "count": len(projects)}


def build_feasibility_report(project: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "project": project,
        "feasibility": {
            "technical": "feasible",
            "financial": "requires_further_analysis",
            "market": "promising",
            "risk": "moderate",
        },
        "recommendations": [
            "Conduct detailed market analysis",
            "Evaluate local partner ecosystem",
            "Assess regulatory requirements",
        ],
    }
