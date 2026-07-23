from __future__ import annotations
from typing import Any


def assess_social_context(channel: str = "wechat", message: str = "", authorization: dict | None = None, evidence: list | None = None, audience: str = "external") -> dict[str, Any]:
    return {
        "ok": True,
        "channel": channel,
        "message_length": len(message),
        "audience": audience,
        "context": {
            "sentiment": "neutral",
            "urgency": "normal",
            "requires_approval": True,
        },
        "evidence_count": len(evidence or []),
    }


def build_authorized_social_reply(channel: str = "wechat", recipient: str = "owner", inbound_message: str = "", authorization: dict | None = None, evidence: list | None = None, audience: str = "external") -> dict[str, Any]:
    return {
        "ok": True,
        "channel": channel,
        "recipient": recipient,
        "draft_reply": f"Thank you for your message regarding: {inbound_message[:100]}",
        "authorization": authorization or {},
        "requires_human_approval": True,
        "evidence_count": len(evidence or []),
        "audience": audience,
    }
