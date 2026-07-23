from __future__ import annotations
from typing import Any
from pathlib import Path
import json
from datetime import datetime


OUTBOX_DIR = Path(__file__).resolve().parents[2] / "comm" / "outbox"


def build_team_response_pack(question: str, metadata: dict | None = None, evidence: list | None = None, persist: bool = False) -> dict[str, Any]:
    pack = {
        "ok": True,
        "question": question,
        "response": {
            "answer": f"Analysis of: {question}",
            "confidence": 0.6,
            "sources": [],
            "recommendations": [
                "Gather additional evidence",
                "Consult domain experts",
                "Review similar cases",
            ],
        },
        "metadata": metadata or {},
        "evidence_count": len(evidence or []),
        "timestamp": datetime.now().isoformat(),
    }
    if persist:
        OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        (OUTBOX_DIR / filename).write_text(json.dumps(pack, indent=2, default=str), encoding="utf-8")
    return pack
