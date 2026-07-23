from __future__ import annotations
from typing import Any
from pathlib import Path
import json
from datetime import datetime


DRAFTS_DIR = Path(__file__).resolve().parents[2] / "comm" / "drafts"


def build_chat_reply_draft(channel: str = "wechat", recipient: str = "owner", message: str = "", context: dict | None = None) -> dict[str, Any]:
    return {
        "channel": channel,
        "recipient": recipient,
        "message": message,
        "context": context or {},
        "draft": f"Reply to {recipient} via {channel}: {message[:200]}",
        "created_at": datetime.now().isoformat(),
        "status": "draft",
        "requires_approval": True,
    }


def save_chat_reply_draft(draft: dict[str, Any]) -> Path:
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"draft_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = DRAFTS_DIR / filename
    path.write_text(json.dumps(draft, indent=2, default=str), encoding="utf-8")
    return path


def send_approved_webhook_message(body: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": True,
        "status": "not_configured",
        "note": "Webhook URL not configured. Set N8N_URL and N8N_API_KEY environment variables.",
        "body": body,
    }
