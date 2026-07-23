from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


LOG_DIR = Path(__file__).resolve().parents[2] / "memory"


def append_audit(
    action: str,
    status: str,
    note: str,
    confidence: int = 0,
    risk: str = "LOW",
    org_id: str = "CODEX",
) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "audit.log"
    timestamp = datetime.now().isoformat(timespec="seconds")
    line = f"{timestamp} | {org_id} | {action} | {confidence} | {risk} | {status} | {note}\n"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)


def read_audit_log(limit: int = 100) -> list[dict[str, Any]]:
    log_path = LOG_DIR / "audit.log"
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    records = []
    for line in lines[-limit:]:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 7:
            records.append({
                "timestamp": parts[0],
                "org_id": parts[1],
                "action": parts[2],
                "confidence": parts[3],
                "risk": parts[4],
                "status": parts[5],
                "note": parts[6],
            })
    return records
