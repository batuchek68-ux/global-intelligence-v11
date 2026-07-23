from __future__ import annotations
from typing import Any


def multi_source_search(query: str) -> dict[str, Any]:
    return {
        "ok": True,
        "query": query,
        "results": {
            "web": [],
            "news": [],
            "trade_databases": [],
            "patents": [],
        },
        "total_results": 0,
        "status": "search_complete",
        "note": "Multi-source search requires configured data source connectors.",
    }
