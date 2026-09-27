from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
REPORT_DIR = BACKEND_ROOT / "reports" / "due_diligence"
sys.path.insert(0, str(REPO_ROOT))


def validate_request(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Request must be a JSON object")
    query = payload.get("query")
    if not isinstance(query, str) or not query.strip() or len(query) > 3000:
        raise ValueError("query must be a non-empty string of at most 3000 characters")
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be a JSON object")

    parties = metadata.get("counterparties", [])
    if isinstance(parties, dict):
        parties = [parties]
    if not isinstance(parties, list) or len(parties) > 20:
        raise ValueError("metadata.counterparties must be a list containing at most 20 parties")

    normalized_parties = []
    for index, party in enumerate(parties):
        if not isinstance(party, dict):
            raise ValueError(f"counterparty {index + 1} must be a JSON object")
        name = party.get("name")
        if not isinstance(name, str) or not name.strip() or len(name) > 300:
            raise ValueError(f"counterparty {index + 1} requires a name of at most 300 characters")
        aliases = party.get("aliases", [])
        if not isinstance(aliases, list) or len(aliases) > 20 or any(
            not isinstance(alias, str) or len(alias) > 300 for alias in aliases
        ):
            raise ValueError(f"counterparty {index + 1} aliases must be a list of at most 20 strings")
        country = party.get("country", "")
        registration_number = party.get("registration_number", "")
        if not isinstance(country, str) or len(country) > 128:
            raise ValueError(f"counterparty {index + 1} country must be a string of at most 128 characters")
        if not isinstance(registration_number, str) or len(registration_number) > 128:
            raise ValueError(f"counterparty {index + 1} registration_number must be a string of at most 128 characters")
        normalized_parties.append({
            "name": name.strip(),
            "aliases": [alias.strip() for alias in aliases if alias.strip()],
            "country": country.strip(),
            "registration_number": registration_number.strip(),
        })

    normalized_metadata = dict(metadata)
    normalized_metadata["counterparties"] = normalized_parties
    if "sanctions_screening_required" in normalized_metadata and not isinstance(
        normalized_metadata["sanctions_screening_required"], bool
    ):
        raise ValueError("metadata.sanctions_screening_required must be a boolean")
    return {
        "query": query.strip(),
        "org_id": str(payload.get("org_id") or "owner")[:128],
        "user_id": str(payload.get("user_id") or "github-actions")[:128],
        "metadata": normalized_metadata,
    }


def _read_request(input_path: str | None) -> dict[str, Any]:
    if input_path:
        raw = Path(input_path).read_text(encoding="utf-8-sig")
    else:
        raw = os.getenv("DUE_DILIGENCE_REQUEST_JSON", "")
    if not raw or len(raw.encode("utf-8")) > 32_000:
        raise ValueError("Provide a JSON request of at most 32 KB using --input or DUE_DILIGENCE_REQUEST_JSON")
    return validate_request(json.loads(raw))


def _write_report(report: dict[str, Any], run_id: str) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    safe_run_id = re.sub(r"[^A-Za-z0-9_.-]", "_", run_id)[:80] or "local"
    json_path = REPORT_DIR / f"due_diligence_{safe_run_id}.json"
    markdown_path = REPORT_DIR / f"due_diligence_{safe_run_id}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    result = report["result"]
    sanctions = result.get("sanctions_screening", {})
    counterparty = result.get("counterparty_verification", {})
    gate = result.get("risk_gate", {})
    decision = result.get("decision", {})
    lines = [
        "# Due Diligence Run",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Execution: `{report['execution_id']}`",
        f"- Query: {report['query']}",
        f"- Orchestration status: `{report['orchestration_status']}`",
        f"- Decision: `{decision.get('decision', 'unknown')}`",
        f"- Human review required: `{str(gate.get('needs_human_approval', True)).lower()}`",
        "",
        "## Sanctions Screening",
        "",
        f"- Status: `{sanctions.get('status', 'missing')}`",
        "- This is not legal clearance. Each individual result and source limitation is in the JSON artifact.",
        "",
        "## Counterparty Verification",
        "",
        f"- Status: `{counterparty.get('status', 'missing')}`",
        "- Identity verification does not establish creditworthiness or performance capability.",
        "",
        "## Next Steps",
        "",
    ]
    for item in decision.get("action_plan", []):
        lines.append(f"- **{item.get('priority', 'normal')}** {item.get('action', 'Review result')}")
    if report.get("learning_recommendations"):
        lines.extend(["", "## Operational Learning", ""])
        lines.extend(f"- {recommendation}" for recommendation in report["learning_recommendations"])
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, markdown_path


async def _execute(request: dict[str, Any]) -> dict[str, Any]:
    sys.path.insert(0, str(REPO_ROOT))
    from api.main import orchestration_engine

    return await orchestration_engine.execute_query(
        query=request["query"],
        org_id=request["org_id"],
        user_id=request["user_id"],
        metadata=request["metadata"],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a v12 due diligence orchestration request")
    parser.add_argument("--input", help="Path to a UTF-8 JSON request file")
    arguments = parser.parse_args()

    try:
        request = _read_request(arguments.input)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        from backend.services.due_diligence_learning_service import record_due_diligence_failure

        record_due_diligence_failure("request_validation", type(error).__name__)
        print(f"Due diligence request rejected: {error}", file=sys.stderr)
        return 2
    try:
        orchestration = asyncio.run(_execute(request))
    except Exception as error:
        from backend.services.due_diligence_learning_service import record_due_diligence_failure

        record_due_diligence_failure("orchestration", type(error).__name__)
        print(f"Due diligence orchestration failed ({type(error).__name__}).", file=sys.stderr)
        return 1

    if orchestration.get("status") != "success":
        from backend.services.due_diligence_learning_service import record_due_diligence_failure

        record_due_diligence_failure("orchestration", "ExecutionFailed")
        print("Due diligence orchestration returned a failed execution status.", file=sys.stderr)
        return 1

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    run_id = os.getenv("GITHUB_RUN_ID") or generated_at.replace(":", "-")
    result = orchestration.get("result", {})
    from backend.services.due_diligence_learning_service import record_due_diligence_outcome

    learning = record_due_diligence_outcome(result)
    report = {
        "generated_at": generated_at,
        "execution_id": orchestration.get("execution_id"),
        "orchestration_status": orchestration.get("status"),
        "query": request["query"],
        "task_count": orchestration.get("task_count"),
        "tasks": orchestration.get("tasks", []),
        "result": result,
        "learning_recommendations": learning["recommendations"],
        "learning_run_count": learning["run_count"],
    }
    json_path, markdown_path = _write_report(report, run_id)
    print(f"Due diligence complete: {result.get('decision', {}).get('decision', 'unknown')}")
    print(f"Sanctions: {result.get('sanctions_screening', {}).get('status', 'missing')}")
    print(f"Counterparty identity: {result.get('counterparty_verification', {}).get('status', 'missing')}")
    print(f"Human review required: {result.get('risk_gate', {}).get('needs_human_approval', True)}")
    print(f"Reports: {json_path}, {markdown_path}")
    print(f"Anonymized learning runs recorded: {learning['run_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())