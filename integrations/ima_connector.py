from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from dotenv import load_dotenv
load_dotenv()


IMA_BASE_URL = "https://ima.qq.com"
IMA_WIKI_PATH = "/openapi/wiki/v1"
IMA_NOTE_PATH = "/openapi/note/v1"


class IMAConnector:
    """腾讯 ima 知识库 / 笔记连接器"""

    def __init__(self, client_id: str | None = None, api_key: str | None = None):
        self.client_id = client_id or os.getenv("IMA_CLIENT_ID", "")
        self.api_key = api_key or os.getenv("IMA_API_KEY", "")
        self.base_url = os.getenv("IMA_BASE_URL", IMA_BASE_URL)

    def configured(self) -> bool:
        return bool(self.client_id and self.api_key)

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "ima-openapi-clientid": self.client_id,
            "ima-openapi-apikey": self.api_key,
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

    # ════════════════════════════════════════════════
    #  知识库 API  (POST /openapi/wiki/v1/...)
    # ════════════════════════════════════════════════

    def list_addable_knowledge_bases(self, cursor: str = "", limit: int = 50) -> dict[str, Any]:
        """列出当前用户可添加内容的知识库"""
        return self._request("POST", f"{IMA_WIKI_PATH}/get_addable_knowledge_base_list",
                             {"cursor": cursor, "limit": limit})

    def list_knowledge_bases(self, query: str = "", cursor: str = "", limit: int = 20) -> dict[str, Any]:
        """搜索知识库列表（query 空时返回可添加列表）"""
        if query:
            return self._request("POST", f"{IMA_WIKI_PATH}/search_knowledge_base",
                                 {"query": query, "cursor": cursor, "limit": limit})
        return self.list_addable_knowledge_bases(cursor, limit)

    def get_knowledge_base(self, kb_ids: list[str]) -> dict[str, Any]:
        """获取知识库详细信息（ids 最多 20 个）"""
        return self._request("POST", f"{IMA_WIKI_PATH}/get_knowledge_base", {"ids": kb_ids})

    def list_knowledge_items(self, kb_id: str, folder_id: str = "", cursor: str = "", limit: int = 50) -> dict[str, Any]:
        """浏览知识库内容（文件和文件夹）"""
        payload = {"knowledge_base_id": kb_id, "cursor": cursor, "limit": limit}
        if folder_id:
            payload["folder_id"] = folder_id
        return self._request("POST", f"{IMA_WIKI_PATH}/get_knowledge_list", payload)

    def search_knowledge(self, kb_id: str, query: str, cursor: str = "") -> dict[str, Any]:
        """在知识库中搜索"""
        return self._request("POST", f"{IMA_WIKI_PATH}/search_knowledge",
                             {"knowledge_base_id": kb_id, "query": query, "cursor": cursor})

    def import_urls(self, kb_id: str, urls: list[str], folder_id: str = "") -> dict[str, Any]:
        """导入网页/微信文章到知识库"""
        payload = {
            "knowledge_base_id": kb_id,
            "folder_id": folder_id or kb_id,
            "urls": urls,
        }
        return self._request("POST", f"{IMA_WIKI_PATH}/import_urls", payload)

    def add_knowledge(self, kb_id: str, title: str, media_type: int,
                      folder_id: str = "", note_info: dict | None = None,
                      web_info: dict | None = None, file_info: dict | None = None,
                      media_id: str = "") -> dict[str, Any]:
        """通用添加知识"""
        payload: dict[str, Any] = {
            "knowledge_base_id": kb_id,
            "media_type": media_type,
            "title": title,
        }
        if folder_id:
            payload["folder_id"] = folder_id
        if media_id:
            payload["media_id"] = media_id
        if note_info:
            payload["note_info"] = note_info
        if web_info:
            payload["web_info"] = web_info
        if file_info:
            payload["file_info"] = file_info
        return self._request("POST", f"{IMA_WIKI_PATH}/add_knowledge", payload)

    def add_note_to_kb(self, kb_id: str, doc_id: str, title: str = "", folder_id: str = "") -> dict[str, Any]:
        """将已有笔记添加到知识库"""
        return self.add_knowledge(
            kb_id=kb_id,
            title=title or doc_id,
            media_type=11,
            folder_id=folder_id,
            note_info={"content_id": doc_id},
        )

    def get_media_info(self, media_id: str) -> dict[str, Any]:
        """获取媒体信息（原文链接等）"""
        return self._request("POST", f"{IMA_WIKI_PATH}/get_media_info", {"media_id": media_id})

    def check_repeated_names(self, kb_id: str, names: list[dict], folder_id: str = "") -> dict[str, Any]:
        """检查文件名是否重复"""
        payload: dict[str, Any] = {"knowledge_base_id": kb_id, "params": names}
        if folder_id:
            payload["folder_id"] = folder_id
        return self._request("POST", f"{IMA_WIKI_PATH}/check_repeated_names", payload)

    def create_media(self, file_name: str, file_size: int, content_type: str,
                     kb_id: str, file_ext: str) -> dict[str, Any]:
        """创建媒体（获取 COS 上传凭证）"""
        return self._request("POST", f"{IMA_WIKI_PATH}/create_media", {
            "file_name": file_name,
            "file_size": file_size,
            "content_type": content_type,
            "knowledge_base_id": kb_id,
            "file_ext": file_ext,
        })

    # ════════════════════════════════════════════════
    #  笔记 API  (POST /openapi/note/v1/...)
    # ════════════════════════════════════════════════

    def search_notes(self, query: str, search_type: int = 0, start: int = 0, end: int = 20) -> dict[str, Any]:
        payload = {"search_type": search_type, "query_info": {"title": query}, "start": start, "end": end}
        return self._request("POST", f"{IMA_NOTE_PATH}/search_note_book", payload)

    def list_note_folders(self, cursor: str = "0", limit: int = 50) -> dict[str, Any]:
        payload = {"cursor": cursor, "limit": limit}
        return self._request("POST", f"{IMA_NOTE_PATH}/list_note_folder_by_cursor", payload)

    def list_notes_in_folder(self, folder_id: str, cursor: str = "", limit: int = 50) -> dict[str, Any]:
        payload = {"folder_id": folder_id, "cursor": cursor, "limit": limit}
        return self._request("POST", f"{IMA_NOTE_PATH}/list_note_by_folder_id", payload)

    def get_note_content(self, doc_id: str, content_format: int = 0) -> dict[str, Any]:
        payload = {"doc_id": doc_id, "target_content_format": content_format}
        return self._request("POST", f"{IMA_NOTE_PATH}/get_doc_content", payload)

    def create_note(self, content: str, folder_id: str = "") -> dict[str, Any]:
        payload: dict[str, Any] = {"content": content, "content_format": 1}
        if folder_id:
            payload["folder_id"] = folder_id
        return self._request("POST", f"{IMA_NOTE_PATH}/import_doc", payload)

    def append_note(self, doc_id: str, content: str) -> dict[str, Any]:
        payload = {"doc_id": doc_id, "content": content, "content_format": 1}
        return self._request("POST", f"{IMA_NOTE_PATH}/append_doc", payload)

    # ════════════════════════════════════════════════
    #  组合操作
    # ════════════════════════════════════════════════

    def sync_note_to_kb(self, kb_id: str, title: str, content: str) -> dict[str, Any]:
        create_result = self.create_note(content)
        if not create_result.get("ok"):
            return create_result
        data = create_result.get("data", {})
        inner = data.get("data", data)
        doc_id = inner.get("note_id", "") or inner.get("doc_id", "")
        if not doc_id:
            return {"ok": False, "error": "Failed to get note_id from created note", "raw": data}
        return self.add_note_to_kb(kb_id, str(doc_id), title)

    def sync_url_to_kb(self, kb_id: str, url: str) -> dict[str, Any]:
        return self.import_urls(kb_id, [url])

    def health_check(self) -> dict[str, Any]:
        if not self.configured():
            return {"ok": False, "status": "not_configured", "message": "Set IMA_CLIENT_ID and IMA_API_KEY"}
        result = self.list_addable_knowledge_bases(limit=1)
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
