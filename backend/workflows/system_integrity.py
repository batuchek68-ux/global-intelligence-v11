from __future__ import annotations
from typing import Any
from pathlib import Path


def run_integrity_check(auto_fix: bool = False) -> dict[str, Any]:
    project_root = Path(__file__).resolve().parents[2]
    checks = {
        "directories": {
            "memory": (project_root / "memory").exists(),
            "reports": (project_root / "reports").exists(),
            "projects": (project_root / "projects").exists(),
            "comm": (project_root / "comm").exists(),
        },
        "config": (project_root / "config.py").exists(),
        "env": (project_root / ".env").exists(),
    }
    all_ok = all(checks.get("directories", {}).values())
    return {
        "ok": all_ok,
        "checks": checks,
        "auto_fix": auto_fix,
        "status": "healthy" if all_ok else "issues_detected",
    }
