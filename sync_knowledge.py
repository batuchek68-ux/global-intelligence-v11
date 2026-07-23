from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from integrations.obsidian_connector import (
    create_daily_note,
    sync_project_to_knowledge,
    sync_intelligence_to_knowledge,
    sync_risk_to_knowledge,
    create_connection_note,
    list_notes,
    KNOWLEDGE_ROOT,
)
from core.storage import ROOT, read_json, write_json


def sync_projects() -> int:
    count = 0
    projects_dir = ROOT / "projects" / "active"
    if projects_dir.exists():
        for f in projects_dir.glob("*.md"):
            content = f.read_text(encoding="utf-8")
            title = f.stem
            country = ""
            for line in content.splitlines():
                if "country" in line.lower() and ":" in line:
                    country = line.split(":", 1)[1].strip()
                    break
            sync_project_to_knowledge({
                "title": title,
                "country": country,
                "status": "active",
                "source_file": str(f),
            })
            count += 1
    project_db = ROOT / "projects" / "library" / "kazakhstan_xinjiang_projects.json"
    if project_db.exists():
        data = read_json(project_db, {})
        for project in data.get("projects", []):
            sync_project_to_knowledge(project)
            count += 1
    return count


def sync_intelligence() -> int:
    count = 0
    reports_dir = ROOT / "reports"
    if reports_dir.exists():
        for f in reports_dir.glob("*.md"):
            if "monitoring" in f.name.lower() or "intelligence" in f.name.lower():
                content = f.read_text(encoding="utf-8")
                sync_intelligence_to_knowledge({
                    "topic": f.stem,
                    "source": "daily_reports",
                    "content_preview": content[:500],
                })
                count += 1
    return count


def sync_risks() -> int:
    count = 0
    memory_dir = ROOT / "memory" / "cases"
    if memory_dir.exists():
        for f in memory_dir.glob("*.json"):
            data = read_json(f, {})
            if "judgment" in data:
                sync_risk_to_knowledge({
                    "title": data.get("project", {}).get("title", f.stem),
                    "level": data["judgment"].get("level", "medium"),
                    "score": data["judgment"].get("score", 0),
                    "triggers": data["judgment"].get("triggers", []),
                })
                count += 1
    return count


def create_daily_knowledge() -> dict:
    result = create_daily_note()
    return result


def run_full_sync() -> dict:
    start = datetime.now()
    projects_synced = sync_projects()
    intelligence_synced = sync_intelligence()
    risks_synced = sync_risks()
    daily = create_daily_knowledge()
    all_notes = list_notes()
    elapsed = (datetime.now() - start).total_seconds()
    return {
        "ok": True,
        "timestamp": start.isoformat(),
        "elapsed_seconds": round(elapsed, 2),
        "projects_synced": projects_synced,
        "intelligence_synced": intelligence_synced,
        "risks_synced": risks_synced,
        "daily_note_created": daily.get("ok", False),
        "total_notes": all_notes.get("count", 0),
    }


if __name__ == "__main__":
    result = run_full_sync()
    print(json.dumps(result, indent=2, ensure_ascii=False))
