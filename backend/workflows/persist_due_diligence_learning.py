from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_FILES = (
    "memory/due_diligence_learning.json",
    "memory/due_diligence_runs.jsonl",
)


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    if os.getenv("GITHUB_ACTIONS") != "true":
        print("Due diligence learning persistence is restricted to GitHub Actions.")
        return 0

    existing_files = tuple(path for path in MEMORY_FILES if (REPO_ROOT / path).is_file())
    if not existing_files:
        print("No due diligence learning state exists; nothing to persist.")
        return 0

    status = run_git("status", "--porcelain", "--", *existing_files)
    if status.returncode:
        print(status.stderr or "Unable to inspect due diligence learning state.")
        return status.returncode
    if not status.stdout.strip():
        print("Due diligence learning state is unchanged.")
        return 0

    for key, value in (
        ("user.name", "github-actions[bot]"),
        ("user.email", "41898282+github-actions[bot]@users.noreply.github.com"),
    ):
        result = run_git("config", key, value)
        if result.returncode:
            print(result.stderr or "Unable to configure GitHub Actions commit identity.")
            return result.returncode

    added = run_git("add", "--", *existing_files)
    if added.returncode:
        print(added.stderr or "Unable to stage due diligence learning state.")
        return added.returncode

    message = os.getenv("STATE_COMMIT_MESSAGE", "Persist anonymized due diligence learning")
    committed = run_git("commit", "--only", "-m", message, "--", *existing_files)
    if committed.returncode:
        print(committed.stderr or committed.stdout or "Unable to persist due diligence learning state.")
        return committed.returncode
    print(committed.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())