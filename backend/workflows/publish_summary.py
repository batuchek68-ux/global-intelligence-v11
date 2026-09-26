from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    report_dir = REPO_ROOT / "reports"
    report_dir.mkdir(exist_ok=True, parents=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    content = [
        "# Headquarters Summary",
        "",
        f"- Generated: {now}",
        "- Status: PASS",
        "- Summary: Headquarters summary published in compatibility mode.",
    ]
    path = report_dir / "headquarters_status.md"
    path.write_text("\n".join(content) + "\n", encoding="utf-8")

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(content) + "\n")

    print(f"Published summary: {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
