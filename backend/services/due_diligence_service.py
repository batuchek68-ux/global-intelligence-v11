# -*- coding: utf-8 -*-
"""Due-diligence service.

Provides conservative, offline-safe screening and counterparty verification
results. External sources can be added behind an explicit integration layer;
this implementation never invents a sanctions match or a verification result.
"""

from __future__ import annotations

from typing import Any, Iterable


def _normalise_name(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def screen_sanctions(entity_name: str, aliases: Iterable[str] | None = None) -> dict[str, Any]:
    """Return an inconclusive sanctions result until authoritative adapters run."""
    name = str(entity_name or "").strip()
    alias_names = [str(alias).strip() for alias in (aliases or []) if str(alias).strip()]
    if not name:
        raise ValueError("entity_name is required")
    return {
        "entity_name": name,
        "aliases": alias_names,
        "status": "inconclusive",
        "matches": [],
        "source_status": "not_configured",
        "recommendation": "Use authoritative sanctions-list adapters and human review before action.",
    }


def verify_counterparty(entity_name: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a verification result without presenting unverified data as facts."""
    name = str(entity_name or "").strip()
    if not name:
        raise ValueError("entity_name is required")
    meta = metadata if isinstance(metadata, dict) else {}
    return {
        "entity_name": name,
        "normalised_name": _normalise_name(name),
        "status": "unavailable",
        "country": str(meta.get("country") or ""),
        "registration_number": str(meta.get("registration_number") or ""),
        "verifications": [],
        "recommendation": "Verify against official registry evidence before commitment.",
    }


__all__ = ["screen_sanctions", "verify_counterparty"]
