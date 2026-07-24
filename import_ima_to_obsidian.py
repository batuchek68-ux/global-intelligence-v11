from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from integrations.ima_connector import get_ima_connector
from integrations.obsidian_connector import sync_to_obsidian, _ensure_dirs


def get_ima_items(kb_id: str) -> list[dict]:
    ima = get_ima_connector()
    all_items = []
    cursor = ""
    
    while True:
        result = ima.list_knowledge_items(kb_id, cursor=cursor, limit=50)
        if not result.get("ok"):
            break
        
        data = result.get("data", {}).get("data", {})
        items = data.get("knowledge_list", [])
        all_items.extend(items)
        
        if data.get("is_end", True):
            break
        cursor = data.get("next_cursor", "")
    
    return all_items


def get_note_content(ima, media_id: str) -> str:
    result = ima.get_media_info(media_id)
    if not result.get("ok"):
        return ""
    
    data = result.get("data", {}).get("data", {})
    url_info = data.get("url_info", {})
    url = url_info.get("url", "")
    
    if url:
        import urllib.request
        try:
            req = urllib.request.Request(url)
            headers = url_info.get("headers", {})
            for k, v in headers.items():
                req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except:
            return f"无法获取内容: {url}"
    
    notebook_ext = data.get("notebook_ext_info", {})
    if notebook_ext.get("notebook_id"):
        return f"[笔记 ID: {notebook_ext['notebook_id']}]"
    
    return "[内容不可用]"


def import_wechat_articles(kb_id: str) -> dict:
    _ensure_dirs()
    ima = get_ima_connector()
    items = get_ima_items(kb_id)
    
    wechat_items = [i for i in items if i.get("media_type") == 6]
    synced = 0
    errors = []
    
    for item in wechat_items:
        media_id = item.get("media_id", "")
        title = item.get("title", "untitled")
        
        content = get_note_content(ima, media_id)
        
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()[:50]
        if not safe_title:
            safe_title = media_id[:20]
        
        note_content = f"""---
title: "{title}"
source: "IMA WeChat Article"
media_id: "{media_id}"
type: "wechat"
imported: "{datetime.now().isoformat()}"
---

# {title}

## 来源

- 微信公众号文章
- IMA 知识库导入

## 内容

{content}

## 相关链接

- [[INDEX|返回首页]]
"""
        
        result = sync_to_obsidian("02-情报", f"wechat-{safe_title}.md", note_content)
        if result.get("ok"):
            synced += 1
        else:
            errors.append({"title": title, "error": result.get("error")})
    
    return {"synced": synced, "errors": errors, "total_wechat": len(wechat_items)}


def import_notes(kb_id: str) -> dict:
    _ensure_dirs()
    ima = get_ima_connector()
    items = get_ima_items(kb_id)
    
    note_items = [i for i in items if i.get("media_type") == 11]
    synced = 0
    errors = []
    
    for item in note_items:
        media_id = item.get("media_id", "")
        title = item.get("title", "untitled")
        
        note_id = media_id.split("_")[-1] if "_" in media_id else media_id
        result = ima.get_note_content(note_id, content_format=0)
        
        content = ""
        if result.get("ok"):
            data = result.get("data", {}).get("data", {})
            content = data.get("content", "")
        
        if not content:
            content = f"[笔记 ID: {note_id}]"
        
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()[:50]
        if not safe_title:
            safe_title = note_id[:20]
        
        note_content = f"""---
title: "{title}"
source: "IMA Note"
note_id: "{note_id}"
type: "note"
imported: "{datetime.now().isoformat()}"
---

# {title}

## 来源

- IMA 笔记
- 自动导入

## 内容

{content}

## 相关链接

- [[INDEX|返回首页]]
"""
        
        result = sync_to_obsidian("02-情报", f"note-{safe_title}.md", note_content)
        if result.get("ok"):
            synced += 1
        else:
            errors.append({"title": title, "error": result.get("error")})
    
    return {"synced": synced, "errors": errors, "total_notes": len(note_items)}


def run_import() -> dict:
    start = datetime.now()
    
    ima = get_ima_connector()
    kb_result = ima.list_addable_knowledge_bases(limit=1)
    kb_list = kb_result.get("data", {}).get("data", {}).get("addable_knowledge_base_list", [])
    
    if not kb_list:
        return {"ok": False, "error": "No knowledge base found"}
    
    kb_id = kb_list[0].get("id", "")
    
    wechat_result = import_wechat_articles(kb_id)
    notes_result = import_notes(kb_id)
    
    elapsed = (datetime.now() - start).total_seconds()
    
    summary_content = f"""---
title: "IMA Import Summary"
type: "import"
date: "{datetime.now().strftime('%Y-%m-%d')}"
created: "{datetime.now().isoformat()}"
---

# IMA 导入摘要

## 导入时间

{datetime.now().isoformat()}

## 导入结果

- **微信文章**: {wechat_result['synced']}/{wechat_result['total_wechat']}
- **笔记**: {notes_result['synced']}/{notes_result['total_notes']}
- **耗时**: {elapsed:.1f} 秒

## 错误

"""
    
    for err in wechat_result.get("errors", []) + notes_result.get("errors", []):
        summary_content += f"- {err.get('title', 'unknown')}: {err.get('error', 'unknown')}\n"
    
    summary_content += """
## 相关链接

- [[INDEX|返回首页]]
"""
    
    sync_to_obsidian("00-首页", "IMA-IMPORT-SUMMARY.md", summary_content)
    
    return {
        "ok": True,
        "timestamp": start.isoformat(),
        "elapsed_seconds": round(elapsed, 2),
        "wechat_synced": wechat_result["synced"],
        "notes_synced": notes_result["synced"],
        "kb_id": kb_id,
    }


if __name__ == "__main__":
    result = run_import()
    print(json.dumps(result, indent=2, ensure_ascii=False))
