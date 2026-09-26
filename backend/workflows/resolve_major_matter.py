from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    report_dir = REPO_ROOT / "reports"
    report_dir.mkdir(exist_ok=True, parents=True)
    payload = {
        "resolved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "ACKNOWLEDGED",
        "summary": "Major matter resolution placeholder accepted in compatibility mode.",
    }
    path = report_dir / "owner_decision.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
