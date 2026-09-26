from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_FILES = (
    "backend/reports/autonomous_repair.json",
    "backend/reports/autonomous_repair.md",
)


def run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def validated_source_files(report: dict[str, object]) -> list[str]:
    changed_files = report.get("changed_files", [])
    if not isinstance(changed_files, list) or any(not isinstance(path, str) for path in changed_files):
        raise ValueError("Repair report has an invalid changed_files list")
    if report.get("status") != "repaired" and changed_files:
        raise ValueError("Repair report lists source changes without a successful repair status")

    source_files: list[str] = []
    for path in changed_files:
        target = (REPO_ROOT / path).resolve()
        if (
            Path(path).as_posix() != path
            or not target.is_relative_to((REPO_ROOT / "backend").resolve())
            or not target.is_file()
        ):
            raise ValueError(f"Repair report contains an unsafe or missing source path: {path}")
        source_files.append(path)
    return source_files


def main() -> int:
    if os.getenv("GITHUB_ACTIONS") != "true":
        print("State persistence is restricted to GitHub Actions; no commit created.")
        return 0

    report_path = REPO_ROOT / EVIDENCE_FILES[0]
    if not report_path.is_file():
        print("No repair report exists; nothing to persist.")
        return 0

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Cannot read repair report; nothing was committed: {error}")
        return 0

    if not report.get("repair_necessary"):
        print("No repair was necessary; report remains available as a workflow artifact.")
        return 0

    try:
        source_files = validated_source_files(report)
    except ValueError as error:
        print(f"{error}; nothing was committed.")
        return 1

    commit_files = (*EVIDENCE_FILES, *source_files)
    status = run_git("status", "--porcelain", "--", *commit_files)
    if status.returncode:
        print(status.stderr or "Unable to inspect repair evidence changes.")
        return status.returncode
    if not status.stdout.strip():
        print("Repair evidence is unchanged; no commit created.")
        return 0

    identity = (
        run_git("config", "user.name", "github-actions[bot]"),
        run_git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"),
    )
    if any(result.returncode for result in identity):
        print("Unable to configure the GitHub Actions commit identity.")
        return 1

    staged = run_git("add", "--", *commit_files)
    if staged.returncode:
        print(staged.stderr or "Unable to stage repair evidence.")
        return staged.returncode

    message = os.getenv("STATE_COMMIT_MESSAGE", "Persist autonomous repair evidence")
    committed = run_git("commit", "--only", "-m", message, "--", *commit_files)
    if committed.returncode:
        print(committed.stderr or committed.stdout or "Unable to commit repair evidence.")
        return committed.returncode
    print(committed.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())