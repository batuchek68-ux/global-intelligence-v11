from __future__ import annotations
from typing import Any
from pathlib import Path


def run_integrity_check(auto_fix: bool = False, project_root: Path | None = None) -> dict[str, Any]:
    project_root = (project_root or Path(__file__).resolve().parents[2]).resolve()
    required_directories = ("memory", "reports", "projects", "comm")
    if auto_fix:
        for name in required_directories:
            directory = (project_root / name).resolve()
            if directory.parent == project_root and not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)

    checks = {
        "directories": {
            name: (project_root / name).is_dir()
            for name in required_directories
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
