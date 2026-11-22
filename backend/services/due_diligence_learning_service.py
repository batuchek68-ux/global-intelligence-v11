from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_DIR = REPO_ROOT / "memory"
RUN_LOG = MEMORY_DIR / "runs.jsonl"
LEARNING_STATE = MEMORY_DIR / "learning.json"


def _ensure_memory() -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not LEARNING_STATE.exists():
        LEARNING_STATE.write_text(
            json.dumps(
                {
                    "run_count": 0,
                    "failed_run_count": 0,
                    "human_review_count": 0,
                    "sanctions_status_counts": {},
                    "sanctions_source_status_counts": {},
                    "recommendations": [],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


def _load_state() -> dict[str, Any]:
    _ensure_memory()
    try:
        data = json.loads(LEARNING_STATE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    state = {
        "run_count": int(data.get("run_count", 0) or 0),
        "failed_run_count": int(data.get("failed_run_count", 0) or 0),
        "human_review_count": int(data.get("human_review_count", 0) or 0),
        "sanctions_status_counts": data.get("sanctions_status_counts") if isinstance(data.get("sanctions_status_counts"), dict) else {},
        "sanctions_source_status_counts": data.get("sanctions_source_status_counts") if isinstance(data.get("sanctions_source_status_counts"), dict) else {},
        "recommendations": data.get("recommendations") if isinstance(data.get("recommendations"), list) else [],
    }
    return state


def _write_state(state: dict[str, Any]) -> None:
    _ensure_memory()
    LEARNING_STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_run_log(entry: dict[str, Any]) -> None:
    _ensure_memory()
    with RUN_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            lower = str(key).lower()
            if lower in {"entity_name", "name", "counterparty", "party_name", "full_name", "customer_name"}:
                continue
            result[key] = _sanitize_value(item)
        return result
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    return value


def _recommendations_for(result: dict[str, Any]) -> list[str]:
    suggestions = [
        "establish authoritative sanctions-list adapters",
        "require human approval before high-risk counterparties are cleared",
        "document evidence provenance and case rationale",
    ]
    if result.get("risk_gate", {}).get("needs_human_approval"):
        suggestions.insert(0, "route blocked decisions to human review")
    return suggestions


def record_due_diligence_outcome(result: dict[str, Any]) -> dict[str, Any]:
    state = _load_state()
    run_count = int(state.get("run_count", 0)) + 1
    state["run_count"] = run_count
    failed_run_count = int(state.get("failed_run_count", 0))
    state["failed_run_count"] = failed_run_count

    sanctions = result.get("sanctions_screening") if isinstance(result, dict) else {}
    if isinstance(sanctions, dict):
        status = str(sanctions.get("status", "unknown"))
        counts = dict(state.get("sanctions_status_counts") or {})
        counts[status] = int(counts.get(status, 0)) + 1
        state["sanctions_status_counts"] = counts

        source_counts: dict[str, dict[str, int]] = defaultdict(dict)
        for screening in sanctions.get("screenings", []) or []:
            if not isinstance(screening, dict):
                continue
            source_status = screening.get("source_status")
            if not isinstance(source_status, dict):
                continue
            for source_name, source_result in source_status.items():
                if not isinstance(source_result, dict):
                    continue
                status_value = str(source_result.get("status", "unknown"))
                bucket = source_counts.get(source_name, {})
                bucket[status_value] = int(bucket.get(status_value, 0)) + 1
                source_counts[source_name] = bucket
        if source_counts:
            merged = dict(state.get("sanctions_source_status_counts") or {})
            for source_name, counts_by_status in source_counts.items():
                merged[source_name] = {**(merged.get(source_name, {})), **{k: int(merged.get(source_name, {}).get(k, 0)) + v for k, v in counts_by_status.items()}}
            state["sanctions_source_status_counts"] = merged

    risk_gate = result.get("risk_gate") if isinstance(result, dict) else {}
    if isinstance(risk_gate, dict) and risk_gate.get("needs_human_approval"):
        state["human_review_count"] = int(state.get("human_review_count", 0)) + 1

    recommendations = _recommendations_for(result if isinstance(result, dict) else {})
    state["recommendations"] = recommendations

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "success",
        "result": _sanitize_value(result),
        "run_count": run_count,
    }
    _append_run_log(entry)
    _write_state(state)
    return {
        "run_count": run_count,
        "failed_run_count": failed_run_count,
        "recommendations": recommendations,
        "human_review_count": state.get("human_review_count", 0),
    }


def record_due_diligence_failure(stage: str, error_type: str) -> dict[str, Any]:
    state = _load_state()
    state["failed_run_count"] = int(state.get("failed_run_count", 0)) + 1
    state["run_count"] = int(state.get("run_count", 0)) + 1
    _write_state(state)

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stage": stage,
        "error_type": error_type,
        "status": "failed",
    }
    _append_run_log(log_entry)
    return {"run_count": state["run_count"], "failed_run_count": state["failed_run_count"]}
