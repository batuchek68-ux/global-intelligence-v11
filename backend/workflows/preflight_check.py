from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_PATHS = [
    ".github/workflows",
    "backend",
    "backend/workflows",
    "backend/reports",
    "reports",
    "memory",
    "docs",
]


def main() -> int:
    missing = []
    for relative in REQUIRED_PATHS:
        if not (REPO_ROOT / relative).exists():
            missing.append(relative)

    status = "PASS" if not missing else "FAIL"
    payload = {
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "missing_paths": missing,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if missing:
        print("Preflight failed: required repository paths are missing.")
        return 1

    print("Preflight passed: required repository paths are present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
