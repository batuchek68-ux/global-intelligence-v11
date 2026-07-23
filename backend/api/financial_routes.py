from __future__ import annotations
from typing import Any
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/v1/financial", tags=["financial"])


@router.post("/payment")
async def process_payment(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return {"ok": True, "payment_id": "payment_stub", "status": "pending_approval", "details": body}


@router.post("/fx-quote")
async def fx_quote(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return {
        "ok": True,
        "from_currency": body.get("from", "USD"),
        "to_currency": body.get("to", "KZT"),
        "rate": 1.0,
        "note": "FX rates require live market data feed.",
    }


@router.post("/credit-assessment")
async def credit_assessment(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return {"ok": True, "entity": body.get("entity", ""), "score": 0.5, "risk_level": "medium"}
