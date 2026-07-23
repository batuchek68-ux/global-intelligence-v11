from __future__ import annotations
from typing import Any
from fastapi import APIRouter, HTTPException, Request

from integrations.ima_connector import get_ima_connector

router = APIRouter(prefix="/v1/ima", tags=["ima"])


@router.get("/health")
async def ima_health() -> dict[str, Any]:
    return get_ima_connector().health_check()


# ── 知识库 ──

@router.get("/kb")
async def ima_list_kbs(query: str = "", cursor: str = "", limit: int = 20) -> dict[str, Any]:
    return get_ima_connector().list_knowledge_bases(query=query, cursor=cursor, limit=limit)


@router.get("/kb/{kb_id}")
async def ima_get_kb(kb_id: str) -> dict[str, Any]:
    return get_ima_connector().get_knowledge_base([kb_id])


@router.get("/kb/{kb_id}/items")
async def ima_list_kb_items(kb_id: str, folder_id: str = "", cursor: str = "", limit: int = 50) -> dict[str, Any]:
    return get_ima_connector().list_knowledge_items(kb_id=kb_id, folder_id=folder_id, cursor=cursor, limit=limit)


@router.post("/kb/search")
async def ima_search_kb(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    kb_id = body.get("kb_id", "")
    query = body.get("query", "")
    if not kb_id or not query:
        raise HTTPException(status_code=400, detail="kb_id and query are required")
    return get_ima_connector().search_knowledge(kb_id=kb_id, query=query)


@router.post("/kb/import-urls")
async def ima_import_urls(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    kb_id = body.get("kb_id", "")
    urls = body.get("urls", [])
    if not kb_id or not urls:
        raise HTTPException(status_code=400, detail="kb_id and urls are required")
    return get_ima_connector().import_urls(kb_id=kb_id, urls=urls, folder_id=body.get("folder_id", ""))


@router.post("/kb/add-note")
async def ima_add_note_to_kb(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    kb_id = body.get("kb_id", "")
    doc_id = body.get("doc_id", "")
    if not kb_id or not doc_id:
        raise HTTPException(status_code=400, detail="kb_id and doc_id are required")
    return get_ima_connector().add_note_to_kb(kb_id=kb_id, doc_id=doc_id, title=body.get("title", ""))


@router.get("/kb/{kb_id}/search")
async def ima_search_in_kb(kb_id: str, query: str, cursor: str = "") -> dict[str, Any]:
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    return get_ima_connector().search_knowledge(kb_id=kb_id, query=query, cursor=cursor)


@router.get("/kb/{kb_id}/media/{media_id}")
async def ima_get_media_info(kb_id: str, media_id: str) -> dict[str, Any]:
    return get_ima_connector().get_media_info(media_id=media_id)


# ── 笔记 ──

@router.get("/notes")
async def ima_list_note_folders(cursor: str = "0", limit: int = 50) -> dict[str, Any]:
    return get_ima_connector().list_note_folders(cursor=cursor, limit=limit)


@router.get("/notes/folder/{folder_id}")
async def ima_list_notes_in_folder(folder_id: str, cursor: str = "", limit: int = 50) -> dict[str, Any]:
    return get_ima_connector().list_notes_in_folder(folder_id=folder_id, cursor=cursor, limit=limit)


@router.post("/notes/search")
async def ima_search_notes(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    query = body.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    return get_ima_connector().search_notes(
        query=query,
        search_type=body.get("search_type", 0),
    )


@router.post("/notes/create")
async def ima_create_note(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    content = body.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    return get_ima_connector().create_note(content=content, folder_id=body.get("folder_id", ""))


@router.post("/notes/append")
async def ima_append_note(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    doc_id = body.get("doc_id", "")
    content = body.get("content", "")
    if not doc_id or not content:
        raise HTTPException(status_code=400, detail="doc_id and content are required")
    return get_ima_connector().append_note(doc_id=doc_id, content=content)


@router.get("/notes/{doc_id}")
async def ima_get_note_content(doc_id: str) -> dict[str, Any]:
    return get_ima_connector().get_note_content(doc_id=doc_id)


# ── 组合同步 ──

@router.post("/sync")
async def ima_sync(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    kb_id = body.get("kb_id", "")
    title = body.get("title", "")
    content = body.get("content", "")
    if not kb_id or not title or not content:
        raise HTTPException(status_code=400, detail="kb_id, title, and content are required")
    return get_ima_connector().sync_note_to_kb(kb_id=kb_id, title=title, content=content)


@router.post("/sync/url")
async def ima_sync_url(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    kb_id = body.get("kb_id", "")
    url = body.get("url", "")
    if not kb_id or not url:
        raise HTTPException(status_code=400, detail="kb_id and url are required")
    return get_ima_connector().sync_url_to_kb(kb_id=kb_id, url=url)
