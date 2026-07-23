from __future__ import annotations

import json
import os
import urllib.request
from typing import Any


IMA_BASE_URL = "https://ima.qq.com"


class IMAConnector:
    """腾讯 ima 知识库连接器"""

    def __init__(self, client_id: str | None = None, api_key: str | None = None):
        self.client_id = client_id or os.getenv("IMA_CLIENT_ID", "")
        self.api_key = api_key or os.getenv("IMA_API_KEY", "")
        self.base_url = os.getenv("IMA_BASE_URL", IMA_BASE_URL)

    def configured(self) -> bool:
        return bool(self.client_id and self.api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Client-Id": self.client_id,
            "X-Api-Key": self.api_key,
        }

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.configured():
            return {"ok": False, "error": "IMA not configured. Set IMA_CLIENT_ID and IMA_API_KEY."}
        data = json.dumps(payload).encode("utf-8") if payload else None
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, data=data, method=method, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8") or "{}"
                result = json.loads(raw)
                return {"ok": True, "data": result, "status": resp.status}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            return {"ok": False, "error": f"HTTP {e.code}: {body}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── 笔记操作 ──

    def search_notes(self, query: str, search_type: int = 0, sort_type: int = 0, start: int = 0, end: int = 20) -> dict[str, Any]:
        payload = {"search_type": search_type, "query": query, "sort_type": sort_type, "start": start, "end": end}
        return self._request("POST", "/api/openapi/note/v1/search_note_book", payload)

    def list_notes(self, cursor: str = "", limit: int = 50) -> dict[str, Any]:
        payload = {"cursor": cursor, "limit": limit}
        return self._request("POST", "/api/openapi/note/v1/get_note_book_list", payload)

    def get_note_content(self, doc_id: str, content_format: int = 2) -> dict[str, Any]:
        payload = {"doc_id": doc_id, "content_format": content_format}
        return self._request("POST", "/api/openapi/note/v1/get_note_content", payload)

    def create_note(self, content: str, folder_id: str = "") -> dict[str, Any]:
        payload = {"content": content}
        if folder_id:
            payload["folder_id"] = folder_id
        return self._request("POST", "/api/openapi/note/v1/create_note", payload)

    def append_note(self, doc_id: str, content: str) -> dict[str, Any]:
        payload = {"doc_id": doc_id, "content": content}
        return self._request("POST", "/api/openapi/note/v1/append_note", payload)

    # ── 知识库操作 ──

    def list_knowledge_bases(self, query: str = "", cursor: str = "", limit: int = 20) -> dict[str, Any]:
        payload = {"query": query, "cursor": cursor, "limit": limit}
        return self._request("POST", "/api/openapi/wiki/v1/search_knowledge_base", payload)

    def search_knowledge(self, kb_id: str, query: str, cursor: str = "", limit: int = 50) -> dict[str, Any]:
        payload = {"kb_id": kb_id, "query": query, "cursor": cursor, "limit": limit}
        return self._request("POST", "/api/openapi/wiki/v1/search_knowledge", payload)

    def list_knowledge_items(self, kb_id: str, folder_id: str = "", cursor: str = "", limit: int = 50) -> dict[str, Any]:
        payload = {"kb_id": kb_id, "cursor": cursor, "limit": limit}
        if folder_id:
            payload["folder_id"] = folder_id
        return self._request("POST", "/api/openapi/wiki/v1/search_knowledge", payload)

    def import_urls(self, kb_id: str, urls: list[str], folder_id: str = "") -> dict[str, Any]:
        payload = {"kb_id": kb_id, "urls": urls}
        if folder_id:
            payload["folder_id"] = folder_id
        return self._request("POST", "/api/openapi/wiki/v1/import_url", payload)

    def create_knowledge_base(self, name: str, description: str = "") -> dict[str, Any]:
        payload = {"name": name}
        if description:
            payload["description"] = description
        return self._request("POST", "/api/openapi/wiki/v1/create_knowledge_base", payload)

    def add_note_to_kb(self, kb_id: str, doc_id: str, title: str = "", folder_id: str = "") -> dict[str, Any]:
        payload = {"kb_id": kb_id, "doc_id": doc_id}
        if title:
            payload["title"] = title
        if folder_id:
            payload["folder_id"] = folder_id
        return self._request("POST", "/api/openapi/wiki/v1/add_knowledge", payload)

    # ── 同步操作 ──

    def sync_note_to_kb(self, kb_id: str, title: str, content: str) -> dict[str, Any]:
        create_result = self.create_note(content)
        if not create_result.get("ok"):
            return create_result
        doc_id = create_result.get("data", {}).get("doc_id", "")
        if not doc_id:
            return {"ok": False, "error": "Failed to get doc_id from created note"}
        return self.add_note_to_kb(kb_id, doc_id, title)

    def sync_url_to_kb(self, kb_id: str, url: str) -> dict[str, Any]:
        return self.import_urls(kb_id, [url])

    def health_check(self) -> dict[str, Any]:
        if not self.configured():
            return {"ok": False, "status": "not_configured", "message": "Set IMA_CLIENT_ID and IMA_API_KEY"}
        result = self.list_knowledge_bases(limit=1)
        return {
            "ok": result.get("ok", False),
            "status": "connected" if result.get("ok") else "error",
            "error": result.get("error"),
        }


_ima: IMAConnector | None = None


def get_ima_connector(client_id: str | None = None, api_key: str | None = None) -> IMAConnector:
    global _ima
    if _ima is None:
        _ima = IMAConnector(client_id, api_key)
    return _ima
