from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
REPORT_DIR = BACKEND_ROOT / "reports"
JSON_REPORT = REPORT_DIR / "autonomous_repair.json"
MARKDOWN_REPORT = REPORT_DIR / "autonomous_repair.md"
MAX_REPAIR_FILES = 5
MAX_SOURCE_BYTES = 100_000


def python_sources(root: Path = BACKEND_ROOT) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def compile_errors(sources: Iterable[Path] | None = None) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for path in sources if sources is not None else python_sources():
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
        except SyntaxError as error:
            errors.append({
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "line": error.lineno,
                "message": error.msg,
            })
        except (OSError, UnicodeError) as error:
            errors.append({
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "line": None,
                "message": f"Unable to read source: {error}",
            })
    return errors


def validate_repair_payload(
    response_text: str,
    expected_paths: set[str],
) -> dict[str, str]:
    payload = json.loads(response_text)
    repairs = payload.get("repairs")
    if not isinstance(repairs, list) or not repairs:
        raise ValueError("The response contains no repair proposals")
    if len(repairs) > MAX_REPAIR_FILES:
        raise ValueError("The response exceeds the repair file limit")

    result: dict[str, str] = {}
    for repair in repairs:
        if not isinstance(repair, dict):
            raise ValueError("Each repair must be an object")
        path = repair.get("path")
        content = repair.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            raise ValueError("Each repair must include a path and full file content")
        normalized = Path(path).as_posix()
        target = (REPO_ROOT / normalized).resolve()
        if normalized != path or not target.is_relative_to(BACKEND_ROOT.resolve()):
            raise ValueError(f"Repair path is outside backend: {path}")
        if path not in expected_paths:
            raise ValueError(f"Repair targets a file without a compile error: {path}")
        if path in result:
            raise ValueError(f"Duplicate repair proposal: {path}")
        if len(content.encode("utf-8")) > MAX_SOURCE_BYTES:
            raise ValueError(f"Repair proposal is too large: {path}")
        result[path] = content

    if set(result) != expected_paths:
        raise ValueError("A proposal is required for every file with a compile error")
    return result


def request_repairs(errors: list[dict[str, Any]], api_key: str) -> dict[str, str]:
    if len(errors) > MAX_REPAIR_FILES:
        raise ValueError("Too many files have compile errors for automatic repair")

    expected_paths = {error["path"] for error in errors}
    source_parts = []
    total_bytes = 0
    for relative_path in sorted(expected_paths):
        source = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        total_bytes += len(source.encode("utf-8"))
        if total_bytes > MAX_SOURCE_BYTES:
            raise ValueError("Affected source exceeds the automatic repair size limit")
        source_parts.append(f"FILE: {relative_path}\n```python\n{source}\n```")

    request_body = {
        "model": os.getenv("OPENAI_MODEL") or "gpt-4o-mini",
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Repair only the reported Python syntax/compilation errors. "
                    "Return JSON exactly shaped as {\"repairs\":[{\"path\":\"backend/...py\","
                    "\"content\":\"complete replacement file\"}]}. Include every requested file "
                    "exactly once. Do not change behavior beyond what is required to restore valid "
                    "Python syntax. Do not add network, shell, credential, publishing, or payment actions."
                ),
            },
            {
                "role": "user",
                "content": json.dumps({"errors": errors, "files": source_parts}, ensure_ascii=False),
            },
        ],
    }
    request = Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"OpenAI API returned HTTP {error.code}: {details}") from error
    except (URLError, TimeoutError) as error:
        raise RuntimeError(f"OpenAI API request failed: {error}") from error

    message = result["choices"][0]["message"]["content"]
    if not isinstance(message, str):
        raise ValueError("OpenAI returned an empty repair response")
    return validate_repair_payload(message, expected_paths)


def run_tests() -> dict[str, Any]:
    tests_dir = BACKEND_ROOT / "tests"
    if not tests_dir.is_dir():
        return {"available": False, "passed": None, "output": "No backend/tests directory"}
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    output = (result.stdout + result.stderr)[-12000:]
    return {"available": True, "passed": result.returncode == 0, "output": output}


def write_report(report: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Autonomous Repair Report",
        "",
        f"- Generated: {report['generated_at']} UTC",
        f"- Status: {report['status']}",
        f"- Repair necessary: {str(report['repair_necessary']).lower()}",
        "",
        "## Compilation",
        "",
    ]
    errors = report["compile_errors"]
    initial_errors = report["initial_compile_errors"]
    if initial_errors:
        lines.extend(
            f"- Initially detected `{item['path']}`:{item['line']}: {item['message']}"
            for item in initial_errors
        )
    else:
        lines.append("- No initial backend Python compile errors detected.")
    if errors:
        lines.append("")
        lines.append("Remaining errors:")
        lines.extend(f"- `{item['path']}`:{item['line']}: {item['message']}" for item in errors)
    else:
        lines.append("- All backend Python files compile successfully after diagnosis.")

    lines.extend(["", "## Repair", ""])
    lines.extend(f"- {item}" for item in report["repair_actions"] or ["No source changes were necessary."])
    lines.extend(["", "## Tests", "", f"- Available: {str(report['tests']['available']).lower()}"])
    if report["tests"]["passed"] is not None:
        lines.append(f"- Passed: {str(report['tests']['passed']).lower()}")
    if report["tests"]["output"]:
        lines.extend(["", "```text", report["tests"]["output"], "```"])
    if report["notes"]:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {note}" for note in report["notes"])

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary_file:
            summary_file.write("\n".join(lines) + "\n")

    MARKDOWN_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    original_errors = compile_errors()
    remaining_errors = original_errors
    repair_actions: list[str] = []
    notes: list[str] = []
    tests: dict[str, Any] = {"available": False, "passed": None, "output": "Not run"}
    status = "healthy"
    snapshots: dict[Path, str] = {}

    if original_errors:
        status = "manual_review_required"
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            notes.append("OPENAI_API_KEY is missing; no source files were changed.")
        else:
            try:
                repairs = request_repairs(original_errors, api_key)
                for relative_path, content in repairs.items():
                    target = REPO_ROOT / relative_path
                    snapshots[target] = target.read_text(encoding="utf-8")
                    target.write_text(content, encoding="utf-8")

                remaining_errors = compile_errors()
                if remaining_errors:
                    raise RuntimeError("The proposed changes did not clear all backend compile errors")

                tests = run_tests()
                if tests["passed"] is False:
                    raise RuntimeError("The test suite failed after the proposed changes")

                status = "repaired"
                repair_actions = [f"Applied and validated repair for `{path}`." for path in sorted(repairs)]
                if not tests["available"]:
                    notes.append("No backend test suite exists; syntax validation was the only repair check.")
            except Exception as error:
                for path, content in snapshots.items():
                    path.write_text(content, encoding="utf-8")
                remaining_errors = compile_errors()
                status = "repair_rejected" if snapshots else "manual_review_required"
                notes.append(f"Automatic repair was not applied: {error}")

    if not original_errors:
        tests = run_tests()
        if tests["passed"] is False:
            status = "tests_failed"
            notes.append("Tests failed; no automated behavioral repair was attempted.")
            notes.append("Human review is required: fix the failing test suite before release or publishing.")
        elif not tests["available"]:
            status = "health_check_only"
            notes.append("No backend test suite exists; syntax validation is the only automated check.")
            notes.append("Human review is recommended before release because real repository tests are not available.")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "repair_necessary": bool(original_errors) or tests["passed"] is False,
        "initial_compile_errors": original_errors,
        "compile_errors": remaining_errors,
        "repair_actions": repair_actions,
        "changed_files": sorted(repairs) if original_errors and status == "repaired" else [],
        "tests": tests,
        "notes": notes,
    }
    write_report(report)
    print(f"Autonomous repair status: {status}")
    print(f"Report: {MARKDOWN_REPORT.relative_to(REPO_ROOT)}")
    if status in {"tests_failed", "health_check_only", "manual_review_required", "repair_rejected"}:
        return 0
    return 1 if report["repair_necessary"] else 0


if __name__ == "__main__":
    raise SystemExit(main())