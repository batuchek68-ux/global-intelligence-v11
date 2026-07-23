from __future__ import annotations
from typing import Any
from fastapi import APIRouter, HTTPException, Request

from integrations.obsidian_connector import (
    read_note,
    write_note,
    list_notes,
    search_notes,
    get_graph,
    create_daily_note,
    create_project_note,
    create_intelligence_note,
    create_risk_note,
    create_connection_note,
    sync_project_to_knowledge,
    sync_intelligence_to_knowledge,
    sync_risk_to_knowledge,
)

router = APIRouter(prefix="/v1/knowledge", tags=["knowledge_base"])


@router.get("/list")
async def knowledge_list(directory: str = "") -> dict[str, Any]:
    return list_notes(directory)


@router.get("/read")
async def knowledge_read(path: str) -> dict[str, Any]:
    if not path:
        raise HTTPException(status_code=400, detail="path is required")
    return read_note(path)


@router.post("/write")
async def knowledge_write(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    path = body.get("path", "")
    content = body.get("content", "")
    frontmatter = body.get("frontmatter") if isinstance(body.get("frontmatter"), dict) else None
    if not path or not content:
        raise HTTPException(status_code=400, detail="path and content are required")
    return write_note(path, content, frontmatter)


@router.post("/search")
async def knowledge_search(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    query = body.get("query", "")
    directory = body.get("directory", "")
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    return search_notes(query, directory)


@router.get("/graph")
async def knowledge_graph() -> dict[str, Any]:
    return get_graph()


@router.post("/daily")
async def create_daily(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    date_str = body.get("date")
    return create_daily_note(date_str)


@router.post("/project")
async def create_project(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    title = body.get("title", "")
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    return create_project_note(
        title=title,
        country=body.get("country", ""),
        industry=body.get("industry", ""),
        details=body,
    )


@router.post("/intelligence")
async def create_intelligence(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    topic = body.get("topic", "")
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")
    return create_intelligence_note(
        topic=topic,
        region=body.get("region", body.get("country", "")),
        source=body.get("source", ""),
    )


@router.post("/risk")
async def create_risk(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    title = body.get("title", "")
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    return create_risk_note(
        title=title,
        risk_level=body.get("risk_level", body.get("level", "medium")),
        category=body.get("category", ""),
    )


@router.post("/connection")
async def create_connection(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    source = body.get("source", "")
    target = body.get("target", "")
    if not source or not target:
        raise HTTPException(status_code=400, detail="source and target are required")
    return create_connection_note(
        source=source,
        target=target,
        relationship=body.get("relationship", ""),
        notes=body.get("notes", ""),
    )


@router.post("/sync/project")
async def sync_project(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return sync_project_to_knowledge(body)


@router.post("/sync/intelligence")
async def sync_intelligence(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return sync_intelligence_to_knowledge(body)


@router.post("/sync/risk")
async def sync_risk(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return sync_risk_to_knowledge(body)
