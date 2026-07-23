from __future__ import annotations
from typing import Any
from pathlib import Path
import json


QUEUE_DIR = Path(__file__).resolve().parents[2] / "memory" / "war_room_queue"


def read_latest_war_room_execution_queue() -> dict[str, Any]:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    queues = sorted(QUEUE_DIR.glob("*.json"), reverse=True)
    if queues:
        try:
            data = json.loads(queues[0].read_text(encoding="utf-8"))
            return {"ok": True, "queue": data}
        except Exception:
            pass
    return {"ok": True, "queue": {"items": [], "status": "empty"}}
