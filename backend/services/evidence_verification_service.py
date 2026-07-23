from __future__ import annotations
from typing import Any


def verify_claim(claim: str, evidence: list | None = None, project: str = "", country: str = "Kazakhstan", persist: bool = False) -> dict[str, Any]:
    evidence = evidence or []
    return {
        "ok": True,
        "claim": claim,
        "project": project,
        "country": country,
        "evidence_count": len(evidence),
        "verification_status": "pending_review",
        "confidence": 0.5,
        "note": "Evidence verification requires external data sources.",
    }
