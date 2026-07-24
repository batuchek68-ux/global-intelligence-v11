from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from integrations.ima_connector import get_ima_connector
from integrations.obsidian_connector import sync_to_obsidian, _ensure_dirs


KB_ID = "Sen0E5DnucfWsOsouYnsiTfrwRdINJY5aarzZiKAUjc="
BASE_URL = "http://localhost:8001"


def get_all_items(folder_id: str = "") -> list[dict]:
    all_items = []
    cursor = ""
    while True:
        url = f"{BASE_URL}/v1/ima/kb/{KB_ID}/items?limit=50&cursor={cursor}"
        if folder_id:
            url += f"&folder_id={folder_id}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())["data"]["data"]
            items = data.get("knowledge_list", [])
            all_items.extend(items)
            if data.get("is_end", True):
                break
            cursor = data.get("next_cursor", "")
    return all_items


def get_note_content(note_id: str) -> str:
    ima = get_ima_connector()
    result = ima.get_note_content(note_id, content_format=0)
    if result.get("ok"):
        data = result.get("data", {}).get("data", {})
        return data.get("content", "")
    return ""


def get_media_content(media_id: str) -> str:
    ima = get_ima_connector()
    result = ima.get_media_info(media_id)
    if not result.get("ok"):
        return ""
    data = result.get("data", {}).get("data", {})
    url_info = data.get("url_info", {})
    url = url_info.get("url", "")
    if url:
        try:
            req = urllib.request.Request(url)
            headers = url_info.get("headers", {})
            for k, v in headers.items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except:
            return f"[无法获取: {url}]"
    notebook_ext = data.get("notebook_ext_info", {})
    if notebook_ext.get("notebook_id"):
        return get_note_content(notebook_ext["notebook_id"])
    return "[内容不可用]"


def safe_filename(title: str, max_len: int = 60) -> str:
    safe = "".join(c for c in title if c.isalnum() or c in " -_中文").strip()
    return safe[:max_len] or "untitled"


def import_item(item: dict, folder_path: str = "") -> bool:
    media_id = item.get("media_id", "")
    title = item.get("title", "untitled")
    media_type = item.get("media_type", 0)

    if media_type == 99:
        return False

    content = get_media_content(media_id)
    fname = safe_filename(title)

    note_content = f"""---
title: "{title}"
media_id: "{media_id}"
media_type: {media_type}
source: "IMA KB"
folder: "{folder_path}"
imported: "{datetime.now().isoformat()}"
---

# {title}

## 来源

- IMA 知识库
- 文件夹: {folder_path or "root"}

## 内容

{content}

## 相关链接

- [[INDEX|返回首页]]
"""

    sub_dir = "02-情报" if media_type == 6 else "06-资源"
    result = sync_to_obsidian(sub_dir, f"{fname}.md", note_content)
    return result.get("ok", False)


def import_folder(folder_id: str, folder_name: str, depth: int = 0) -> dict:
    items = get_all_items(folder_id)
    synced = 0
    skipped = 0

    for item in items:
        if item.get("media_type") == 99:
            sub_id = item["media_id"]
            sub_name = item.get("title", "unknown")
            result = import_folder(sub_id, sub_name, depth + 1)
            synced += result.get("synced", 0)
        else:
            if import_item(item, folder_name):
                synced += 1
            else:
                skipped += 1

    return {"synced": synced, "skipped": skipped}


def run_full_import() -> dict:
    _ensure_dirs()
    start = datetime.now()

    root_items = get_all_items()
    synced = 0
    total = 0

    for item in root_items:
        total += 1
        if item.get("media_type") == 99:
            folder_id = item["media_id"]
            folder_name = item.get("title", "unknown")
            print(f"Entering folder: {folder_name}")
            result = import_folder(folder_id, folder_name)
            synced += result.get("synced", 0)
        else:
            if import_item(item, "root"):
                synced += 1

    elapsed = (datetime.now() - start).total_seconds()

    summary = f"""---
title: "Full IMA Import"
type: "import"
date: "{datetime.now().strftime('%Y-%m-%d')}"
created: "{datetime.now().isoformat()}"
---

# IMA 全量导入

## 结果

- **总计**: {total} 个根项目
- **成功**: {synced} 个文档
- **耗时**: {elapsed:.1f} 秒
- **时间**: {datetime.now().isoformat()}

## 相关链接

- [[INDEX|返回首页]]
"""
    sync_to_obsidian("00-首页", "FULL-IMPORT-SUMMARY.md", summary)

    return {
        "ok": True,
        "timestamp": start.isoformat(),
        "elapsed_seconds": round(elapsed, 2),
        "total_root": total,
        "synced": synced,
    }


if __name__ == "__main__":
    result = run_full_import()
    print(json.dumps(result, indent=2, ensure_ascii=False))
