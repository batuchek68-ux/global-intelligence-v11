from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from integrations.obsidian_connector import (
    sync_to_obsidian,
    OBSIDIAN_VAULT,
    _ensure_dirs,
)


def get_git_changes(count: int = 10) -> list[dict]:
    result = subprocess.run(
        ["git", "log", f"-{count}", "--pretty=format:%H|%s|%ai"],
        capture_output=True, text=True, encoding="utf-8"
    )
    changes = []
    for line in result.stdout.strip().split("\n"):
        if "|" in line:
            parts = line.split("|", 2)
            if len(parts) >= 2:
                changes.append({
                    "hash": parts[0][:8],
                    "message": parts[1],
                    "date": parts[2] if len(parts) > 2 else "",
                })
    return changes


def get_changed_files(commit_hash: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
        capture_output=True, text=True, encoding="utf-8"
    )
    return [f for f in result.stdout.strip().split("\n") if f]


def create_commit_note(commit: dict, files: list[str]) -> str:
    date_str = commit["date"][:10] if commit["date"] else datetime.now().strftime("%Y-%m-%d")
    file_list = "\n".join([f"- `{f}`" for f in files[:20]])
    
    return f"""---
title: "{commit['message']}"
commit: "{commit['hash']}"
date: "{date_str}"
type: changelog
created: "{datetime.now().isoformat()}"
---

# {commit['message']}

## 提交信息

- **Commit**: `{commit['hash']}`
- **日期**: {date_str}
- **消息**: {commit['message']}

## 变更文件

{file_list}

## 相关链接

- [[INDEX|返回首页]]
"""


def sync_git_to_obsidian(count: int = 10) -> dict:
    _ensure_dirs()
    changes = get_git_changes(count)
    synced = 0
    
    for commit in changes:
        files = get_changed_files(commit["hash"])
        if not files:
            continue
        
        content = create_commit_note(commit, files)
        filename = f"{commit['date'][:10]}-{commit['hash']}.md" if commit["date"] else f"{commit['hash']}.md"
        
        result = sync_to_obsidian("06-资源", filename, content)
        if result.get("ok"):
            synced += 1
    
    return {"ok": True, "synced": synced, "total_changes": len(changes)}


def create_system_memory() -> str:
    return f"""---
title: System Memory
type: memory
created: "{datetime.now().isoformat()}"
---

# System Memory

## 自动同步规则

1. **GitHub 提交** → 自动同步到 `06-资源` 文件夹
2. **项目变更** → 自动同步到 `01-项目` 文件夹
3. **风险更新** → 自动同步到 `03-风险` 文件夹
4. **每日笔记** → 自动同步到 `04-每日` 文件夹

## 文件夹结构

- `00-首页` - 系统概览和导航
- `01-项目` - 项目文档
- `02-情报` - 市场情报
- `03-风险` - 风险评估
- `04-每日` - 每日笔记
- `05-协议` - 操作协议
- `06-资源` - 工具和变更日志
- `07-存档` - 历史存档

## 同步状态

- **IMA 知识库**: 已连接
- **Obsidian Vault**: 已同步
- **自动同步**: 已启用

## 最后更新

{datetime.now().isoformat()}
"""


def init_memory() -> dict:
    _ensure_dirs()
    content = create_system_memory()
    result = sync_to_obsidian("00-首页", "MEMORY.md", content)
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        result = init_memory()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        result = sync_git_to_obsidian(20)
        print(json.dumps(result, indent=2, ensure_ascii=False))
