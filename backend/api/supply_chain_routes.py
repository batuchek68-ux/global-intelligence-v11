from __future__ import annotations
from typing import Any
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/v1/supply-chain", tags=["supply_chain"])


@router.post("/track")
async def track_shipment(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    shipment_id = body.get("shipment_id", "unknown")
    return {
        "ok": True,
        "shipment_id": shipment_id,
        "status": "not_tracked",
        "milestones": [],
        "note": "Supply chain tracking requires external logistics integration.",
    }


@router.get("/status")
async def supply_chain_status() -> dict[str, Any]:
    return {"ok": True, "active_shipments": 0, "status": "idle"}
