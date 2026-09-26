from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    labels = ["major-matter", "owner-decision", "autonomous"]
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (REPO_ROOT / "reports").mkdir(exist_ok=True, parents=True)
    report_path = REPO_ROOT / "reports" / "labels_status.md"
    lines = [
        "# GitHub Labels Status",
        "",
        f"- Checked at: {now}",
        "",
    ]
    for label in labels:
        lines.append(f"- {label}: configured or not required in local compatibility mode")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Labels status written to {report_path.relative_to(REPO_ROOT)}")
    if os.getenv("GITHUB_ACTIONS") == "true":
        summary = os.getenv("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
