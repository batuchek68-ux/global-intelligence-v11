from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
MEMORY_DIR = REPO_ROOT / "memory"
RUN_LOG = MEMORY_DIR / "due_diligence_runs.jsonl"
LEARNING_STATE = MEMORY_DIR / "due_diligence_learning.json"
_LOCK = RLock()


def _counts(value: Any) -> Counter[str]:
    if isinstance(value, dict):
        status = value.get("status") or value.get("screening_status") or value.get("identity_status")
        return Counter({str(status): 1}) if status else Counter()
    if isinstance(value, list):
        counts: Counter[str] = Counter()
        for item in value:
            counts.update(_counts(item))
        return counts
    return Counter()


def _sanctions_source_status(screening: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in screening.get("screenings", []):
        if not isinstance(item, dict):
            continue
        for jurisdiction, source in item.get("source_status", {}).items():
            if isinstance(source, dict):
                result[jurisdiction] = str(source.get("status", "unknown"))
    return result


def _recommendations(state: dict[str, Any]) -> list[str]:
    sanctions = state["sanctions_status_counts"]
    counterparties = state["counterparty_status_counts"]
    recommendations = []
    unresolved_sanctions = sum(sanctions.get(status, 0) for status in ("inconclusive", "unavailable"))
    if unresolved_sanctions:
        recommendations.append(
            "Connect and monitor authoritative sanctions-list adapters; unresolved checks must remain subject to human review."
        )
    unresolved_identity = sum(
        counterparties.get(status, 0)
        for status in ("partial", "unverified", "conflicting", "unavailable")
    )
    if unresolved_identity:
        recommendations.append(
            "Prioritize official company-registry adapters and reconcile identity conflicts before external commitments."
        )
    if not recommendations:
        recommendations.append("Continue collecting outcomes; no evidence-backed workflow change is indicated yet.")
    return recommendations


def _load_learning_state() -> dict[str, Any]:
    if LEARNING_STATE.is_file():
        try:
            state = json.loads(LEARNING_STATE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            state = {}
    else:
        state = {}
    if not isinstance(state, dict):
        state = {}

    state.setdefault("schema_version", 1)
    for key in ("run_count", "failed_run_count", "human_review_count"):
        if not isinstance(state.get(key), int) or state[key] < 0:
            state[key] = 0
    for key in ("sanctions_status_counts", "counterparty_status_counts", "sanctions_source_status_counts"):
        if not isinstance(state.get(key), dict):
            state[key] = {}
    return state


def record_due_diligence_failure(stage: str, error_type: str) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    observation = {
        "recorded_at": timestamp,
        "run_status": "failed",
        "stage": stage[:64],
        "error_type": error_type[:96],
    }
    with _LOCK:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        with RUN_LOG.open("a", encoding="utf-8") as log:
            log.write(json.dumps(observation, ensure_ascii=False, separators=(",", ":")) + "\n")

        state = _load_learning_state()
        state["run_count"] += 1
        state["failed_run_count"] += 1
        state["updated_at"] = timestamp
        state["privacy"] = "Aggregates and status-only run log; no query, party name, alias, or registration number is stored."
        state["recommendations"] = [
            f"Investigate repeated due diligence runner failures at stage `{stage[:64]}` (error type: `{error_type[:96]}`); no request content was persisted."
        ]
        temporary = LEARNING_STATE.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(LEARNING_STATE)
    return {"run_count": state["run_count"], "failed_run_count": state["failed_run_count"]}


def record_due_diligence_outcome(result: dict[str, Any]) -> dict[str, Any]:
    sanctions = result.get("sanctions_screening", {}) if isinstance(result, dict) else {}
    counterparties = result.get("counterparty_verification", {}) if isinstance(result, dict) else {}
    gate = result.get("risk_gate", {}) if isinstance(result, dict) else {}
    sanctions_counts = _counts(sanctions)
    counterparty_counts = _counts(counterparties)
    source_status = _sanctions_source_status(sanctions)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    observation = {
        "recorded_at": timestamp,
        "sanctions_status": sanctions.get("status", "missing"),
        "counterparty_status": counterparties.get("status", "missing"),
        "human_review_required": bool(gate.get("needs_human_approval", True)),
        "sanctions_source_status": source_status,
    }

    with _LOCK:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        with RUN_LOG.open("a", encoding="utf-8") as log:
            log.write(json.dumps(observation, ensure_ascii=False, separators=(",", ":")) + "\n")

        state = _load_learning_state()
        state["run_count"] += 1
        state["human_review_count"] += int(observation["human_review_required"])

        for key, counts in (
            ("sanctions_status_counts", sanctions_counts),
            ("counterparty_status_counts", counterparty_counts),
        ):
            totals = Counter(state[key])
            totals.update(counts)
            state[key] = dict(sorted(totals.items()))

        source_totals = state["sanctions_source_status_counts"]
        for jurisdiction, status in source_status.items():
            counts = Counter(source_totals.get(jurisdiction, {}))
            counts[status] += 1
            source_totals[jurisdiction] = dict(sorted(counts.items()))

        state["updated_at"] = timestamp
        state["privacy"] = "Aggregates and status-only run log; no query, party name, alias, or registration number is stored."
        state["recommendations"] = _recommendations(state)
        temporary = LEARNING_STATE.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(LEARNING_STATE)

    return {
        "run_count": state["run_count"],
        "recommendations": list(state["recommendations"]),
        "human_review_count": state["human_review_count"],
    }