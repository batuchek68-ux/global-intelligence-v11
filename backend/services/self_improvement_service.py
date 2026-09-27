from __future__ import annotations
from typing import Any
from pathlib import Path
import json
from datetime import datetime
from threading import RLock


STATE_FILE = Path(__file__).resolve().parents[2] / "memory" / "self_improvement.json"
_STATE_LOCK = RLock()
REASONING_METHODS = {
    "first_principles": "Separate directly evidenced constraints from assumptions.",
    "falsification": "Identify evidence that could disprove the leading interpretation.",
    "second_order_effects": "Trace downstream costs, dependencies, and unintended consequences.",
    "base_rates": "Compare with relevant historical cases before estimating likelihood.",
    "reversibility": "Prefer a reversible information-gathering action while uncertainty is high.",
}
METHOD_FEEDBACK_OUTCOMES = {"helpful", "not_helpful", "inconclusive"}


def _empty_state() -> dict[str, Any]:
    return {
        "cycles": 0,
        "improvements": [],
        "status": "initialized",
        "metrics": {"executions": 0, "average_evidence_quality": None, "providers": {}},
        "method_feedback": [],
    }


def _load_state() -> dict[str, Any]:
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            if isinstance(state, dict):
                defaults = _empty_state()
                for key, value in defaults.items():
                    state.setdefault(key, value)
                if not isinstance(state.get("metrics"), dict):
                    state["metrics"] = defaults["metrics"]
                if not isinstance(state.get("improvements"), list):
                    state["improvements"] = []
                if not isinstance(state.get("method_feedback"), list):
                    state["method_feedback"] = []
                state["metrics"].setdefault("executions", 0)
                state["metrics"].setdefault("average_evidence_quality", None)
                if not isinstance(state["metrics"].get("providers"), dict):
                    state["metrics"]["providers"] = {}
                return state
        except Exception:
            pass
    return _empty_state()


def _save_state(state: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = STATE_FILE.with_suffix(".tmp")
    temporary_file.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    temporary_file.replace(STATE_FILE)


def read_self_improvement_state() -> dict[str, Any]:
    return {"ok": True, "state": _load_state()}


def build_self_improvement_plan(evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    state = _load_state()
    metrics = state["metrics"]
    quality = metrics.get("average_evidence_quality")
    recommendations = []
    providers = metrics.get("providers", {})
    if not metrics.get("executions"):
        recommendations.append("Collect real query outcomes before tuning agent behavior.")
    if quality is not None and quality < 0.6:
        recommendations.append("Increase source coverage and route low-evidence answers to human review.")
    for name, status in providers.items():
        if status.get("failures", 0) > status.get("successes", 0):
            recommendations.append(f"Investigate provider availability: {name}.")
    for item in providers.values():
        if item.get("credential_env"):
            recommendations.append(f"Configure optional search credential: {item['credential_env']}.")
    if not recommendations:
        recommendations.append("Continue collecting outcomes; no evidence-backed change is currently indicated.")
    method_feedback = state.get("method_feedback", [])
    method_learning = []
    for method, description in REASONING_METHODS.items():
        records = [item for item in method_feedback if item.get("method") == method]
        considered = [item for item in records if item.get("outcome") != "inconclusive"]
        helpful_count = sum(item["outcome"] == "helpful" for item in considered)
        helpful_rate = round(helpful_count / len(considered), 3) if considered else None
        method_learning.append({
            "method": method,
            "description": description,
            "feedback_count": len(records),
            "helpful_rate": helpful_rate,
            "status": "provisional" if len(considered) < 5 else "evidence_observed",
        })
        if len(considered) >= 5 and helpful_rate is not None and helpful_rate < 0.5:
            recommendations.append(f"Review when and how the {method} lens is applied; observed helpful rate is low.")
    plan = {
        "ok": True,
        "cycle": state.get("cycles", 0) + 1,
        "areas": [
            {"area": "agent_accuracy", "current_score": None, "target_score": 0.85, "status": "not_measured"},
            {"area": "response_time", "current_score": None, "target_score": 0.8, "status": "not_measured"},
            {"area": "evidence_quality", "current_score": quality, "target_score": 0.75},
        ],
        "metrics": metrics,
        "recommendations": recommendations,
        "reasoning_method_learning": method_learning,
        "automation_boundary": "Recommendations are recorded; source code and external actions require human approval.",
        "evidence": evidence,
    }
    return plan


def run_self_improvement_cycle(evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    with _STATE_LOCK:
        state = _load_state()
        plan = build_self_improvement_plan(evidence)
        state["cycles"] = state.get("cycles", 0) + 1
        status = "recommendations_generated" if state["metrics"].get("executions") else "insufficient_observations"
        improvement = {
            "cycle": state["cycles"],
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "recommendations": plan["recommendations"],
        }
        state["improvements"].append(improvement)
        state["status"] = status
        _save_state(state)
        return {"ok": True, "cycle": state["cycles"], "status": status, "metrics": state["metrics"], "recommendations": plan["recommendations"]}


def record_execution_outcome(result: dict[str, Any]) -> None:
    evidence = result.get("evidence_quality") if isinstance(result, dict) else None
    if not isinstance(evidence, dict):
        return
    score = evidence.get("quality_score")
    if not isinstance(score, (int, float)):
        return

    with _STATE_LOCK:
        state = _load_state()
        metrics = state["metrics"]
        previous_average = metrics.get("average_evidence_quality")
        metrics["executions"] += 1
        metrics["average_evidence_quality"] = round(
            float(score) if previous_average is None else 0.8 * float(previous_average) + 0.2 * float(score),
            3,
        )
        for name, provider in evidence.get("provider_status", {}).items():
            current = metrics["providers"].setdefault(name, {"successes": 0, "failures": 0, "credential_env": None})
            status = provider.get("status")
            if status == "ok":
                current["successes"] += 1
            elif status == "error":
                current["failures"] += 1
            if provider.get("credential_env"):
                current["credential_env"] = provider["credential_env"]
        state["status"] = "observing"
        _save_state(state)


def record_method_feedback(feedback: dict[str, Any]) -> dict[str, Any]:
    method = feedback.get("method")
    outcome = feedback.get("outcome")
    evidence = feedback.get("evidence")
    if method not in REASONING_METHODS:
        raise ValueError("method is not in the supported reasoning method catalog")
    if outcome not in METHOD_FEEDBACK_OUTCOMES:
        raise ValueError("outcome must be helpful, not_helpful, or inconclusive")
    if not isinstance(evidence, str) or not 12 <= len(evidence.strip()) <= 2000:
        raise ValueError("evidence must contain 12 to 2000 characters")

    record = {
        "method": method,
        "outcome": outcome,
        "evidence": evidence.strip(),
        "execution_id": str(feedback.get("execution_id") or "")[:128],
        "recorded_at": datetime.now().isoformat(),
    }
    with _STATE_LOCK:
        state = _load_state()
        state["method_feedback"].append(record)
        state["method_feedback"] = state["method_feedback"][-500:]
        state["status"] = "learning_from_human_feedback"
        _save_state(state)
    return {"ok": True, "recorded": {key: value for key, value in record.items() if key != "evidence"}, "status": state["status"]}
