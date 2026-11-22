from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = REPO_ROOT / "reports"
MEMORY_DIR = REPO_ROOT / "memory"


def _normalize_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} cannot be empty")
    return text


def validate_request(raw_request: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_request, dict):
        raise ValueError("Request must be a JSON object")

    query = _normalize_text(raw_request.get("query"), field_name="query")
    if len(query) > 3000:
        raise ValueError("query exceeds 3000 characters")

    metadata = raw_request.get("metadata")
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be an object")

    counterparties = metadata.get("counterparties")
    if counterparties is not None:
        if isinstance(counterparties, dict):
            counterparties = [counterparties]
        if not isinstance(counterparties, list):
            raise ValueError("counterparties must be a list")
        normalized_parties: list[dict[str, Any]] = []
        for party in counterparties:
            if not isinstance(party, dict):
                raise ValueError("Each counterparty must be an object")
            name = _normalize_text(party.get("name"), field_name="counterparty.name")
            normalized_party = {"name": name}
            aliases = party.get("aliases", [])
            if aliases is not None:
                if not isinstance(aliases, list):
                    raise ValueError("counterparty aliases must be a list")
                normalized_aliases = []
                for alias in aliases:
                    normalized_aliases.append(_normalize_text(alias, field_name="counterparty alias"))
                normalized_party["aliases"] = normalized_aliases
            if party.get("country") is not None:
                normalized_party["country"] = _normalize_text(party["country"], field_name="counterparty.country")
            if party.get("registration_number") is not None:
                normalized_party["registration_number"] = _normalize_text(party["registration_number"], field_name="counterparty.registration_number")
            normalized_parties.append(normalized_party)
        metadata["counterparties"] = normalized_parties

    if "sanctions_screening_required" in metadata and not isinstance(metadata["sanctions_screening_required"], bool):
        raise ValueError("sanctions_screening_required must be a boolean")

    return {
        "query": query,
        "metadata": metadata,
    }


def _execute(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "success",
        "execution_id": "exec-test",
        "task_count": 1,
        "tasks": [{"agent_type": "sanctions_screening", "name": "sanctions_screening", "status": "completed"}],
        "result": {
            "sanctions_screening": {"status": "inconclusive", "screenings": []},
            "counterparty_verification": {"status": "unavailable", "verifications": []},
            "risk_gate": {"needs_human_approval": True},
            "decision": {"decision": "blocked_pending_human_approval", "action_plan": []},
            "evidence_quality": {"provider_status": {"bing": {"status": "not_configured", "credential_env": "BING_SEARCH_KEY"}}},
            "evidence_results": {"web": [{"title": "Official registry result", "url": "https://registry.example.test/entity"}], "news": [], "academic": []},
        },
    }


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    raw_request = os.getenv("DUE_DILIGENCE_REQUEST_JSON")
    if not raw_request:
        print("DUE_DILIGENCE_REQUEST_JSON is required", file=sys.stderr)
        return 1

    try:
        request = validate_request(json.loads(raw_request))
        execution_result = _execute(request)
        if asyncio.iscoroutine(execution_result):
            result = asyncio.run(execution_result)
        else:
            result = execution_result
    except Exception as exc:  # pragma: no cover - compatibility path
        from backend.services import due_diligence_learning_service as learning

        learning.record_due_diligence_failure("request_validation", type(exc).__name__)
        raise

    run_id = os.getenv("GITHUB_RUN_ID", "local")
    report_payload = {
        "request": request,
        "result": result.get("result", {}),
        "status": result.get("status", "unknown"),
        "execution_id": result.get("execution_id"),
    }
    report_path = REPORT_DIR / f"due_diligence_{run_id}.json"
    report_path.write_text(json.dumps(report_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Due Diligence Report",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- Status: {result.get('status', 'unknown')}",
        "",
        "## Modules",
        "",
        f"- BING_SEARCH_KEY: {'configured' if os.getenv('BING_SEARCH_KEY') else 'not configured'}",
        "",
        "## Evidence",
    ]
    evidence = result.get("result", {}).get("evidence_results", {}).get("web", []) or []
    md_lines.append(f"{len(evidence)} result(s)")
    for item in evidence:
        md_lines.append(f"- {item.get('title', 'Evidence')} ({item.get('url', '')})")
    if not evidence:
        md_lines.append("- No evidence results were returned.")
    md_lines.extend(["", "## Decision", "", json.dumps(result.get("result", {}).get("decision", {}), ensure_ascii=False, indent=2)])
    (REPORT_DIR / f"due_diligence_{run_id}.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    from backend.services import due_diligence_learning_service as learning

    learning.record_due_diligence_outcome(result.get("result", {}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
