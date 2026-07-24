from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from integrations.obsidian_connector import sync_to_obsidian, _ensure_dirs
from integrations.ima_connector import get_ima_connector


def search_internet_topics() -> list[dict]:
    topics = [
        {"query": "哈萨克斯坦 矿业 投资 2024", "region": "Kazakhstan", "type": "market"},
        {"query": "新疆 口岸 贸易 最新政策", "region": "Xinjiang", "type": "policy"},
        {"query": "中亚 基础设施 项目", "region": "Central Asia", "type": "infrastructure"},
        {"query": "国际贸易 AI 应用", "region": "Global", "type": "technology"},
        {"query": "一带一路 最新进展", "region": "BRI", "type": "policy"},
    ]
    return topics


def create_intelligence_note(topic: dict, content: str = "") -> dict:
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-{topic['type']}-{topic['region']}.md"
    
    note_content = f"""---
title: "{topic['query']}"
region: "{topic['region']}"
type: "{topic['type']}"
date: "{date_str}"
created: "{datetime.now().isoformat()}"
---

# {topic['query']}

## 地区
{topic['region']}

## 类型
{topic['type']}

## 内容

{content or "等待搜索填充..."}

## 来源

- IMA 知识库
- 互联网搜索

## 相关链接

- [[INDEX|返回首页]]
"""
    
    return sync_to_obsidian("02-情报", filename, note_content)


def run_cron() -> dict:
    _ensure_dirs()
    
    ima = get_ima_connector()
    ima_status = "connected" if ima.configured() else "not_configured"
    
    topics = search_internet_topics()
    synced = 0
    
    for topic in topics:
        result = create_intelligence_note(topic)
        if result.get("ok"):
            synced += 1
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    daily_content = f"""---
title: "V11 Cron - {date_str}"
type: "cron"
date: "{date_str}"
created: "{datetime.now().isoformat()}"
---

# V11 自动任务 - {date_str}

## 执行状态

- **IMA**: {ima_status}
- **情报同步**: {synced}/{len(topics)}
- **执行时间**: {datetime.now().isoformat()}

## 待搜索主题

"""
    for topic in topics:
        daily_content += f"- [{topic['region']}] {topic['query']}\n"
    
    daily_content += f"""

## 下次执行

30 分钟后自动执行

## 相关链接

- [[INDEX|返回首页]]
"""
    
    sync_to_obsidian("04-每日", f"{date_str}-cron.md", daily_content)
    
    return {
        "ok": True,
        "timestamp": datetime.now().isoformat(),
        "ima_status": ima_status,
        "topics_synced": synced,
        "total_topics": len(topics),
    }


if __name__ == "__main__":
    result = run_cron()
    print(json.dumps(result, indent=2, ensure_ascii=False))
