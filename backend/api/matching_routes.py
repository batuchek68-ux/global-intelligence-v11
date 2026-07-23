from __future__ import annotations
from typing import Any
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/v1/matching", tags=["matching"])


@router.post("/find")
async def find_matches(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    query = str(body.get("query") or body.get("q") or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    return {
        "ok": True,
        "query": query,
        "matches": [],
        "total": 0,
        "note": "Matching engine requires configured buyer/supplier database.",
    }


@router.post("/quote")
async def create_quote(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return {"ok": True, "quote_id": "quote_stub", "status": "draft", "details": body}
