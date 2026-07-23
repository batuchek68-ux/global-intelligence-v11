from __future__ import annotations
from typing import Any
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/v1/integrations", tags=["integrations"])


@router.post("/n8n/trigger/{workflow_id}")
async def trigger_n8n(workflow_id: str, request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return {
        "ok": False,
        "status": "not_configured",
        "workflow_id": workflow_id,
        "note": "n8n integration requires N8N_URL and N8N_API_KEY environment variables.",
    }


@router.get("/n8n/status")
async def n8n_status() -> dict[str, Any]:
    return {"ok": True, "configured": False, "status": "not_configured"}
