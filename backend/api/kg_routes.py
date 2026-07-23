from __future__ import annotations
from typing import Any
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/v1/kg", tags=["knowledge_graph"])


@router.post("/query")
async def kg_query(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    query = body.get("query", "")
    return {
        "ok": True,
        "query": query,
        "nodes": [],
        "relationships": [],
        "note": "Knowledge graph requires Neo4j or file-based backend.",
    }


@router.get("/stats")
async def kg_stats() -> dict[str, Any]:
    return {"ok": True, "nodes": 0, "relationships": 0, "status": "empty"}
