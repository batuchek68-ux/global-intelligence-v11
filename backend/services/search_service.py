from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT = 8
DEFAULT_LIMIT = 5


def _request_json(url: str, headers: dict[str, str] | None = None, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "GlobalIntelligenceV11/1.0", **(headers or {})})
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Search provider returned a non-object response")
    return payload


def _item(title: Any, url: Any, snippet: Any, provider: str, published_at: Any = None) -> dict[str, Any] | None:
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        return None
    return {
        "title": str(title or url),
        "url": url,
        "snippet": str(snippet or ""),
        "source": provider,
        "published_at": str(published_at) if published_at else None,
    }


def _bing(query: str, limit: int, timeout: int) -> list[dict[str, Any]]:
    key = os.getenv("BING_SEARCH_KEY")
    if not key:
        return []
    url = "https://api.bing.microsoft.com/v7.0/search?" + urlencode({"q": query, "count": limit})
    payload = _request_json(url, {"Ocp-Apim-Subscription-Key": key}, timeout)
    entries = payload.get("webPages", {}).get("value", [])
    return [result for row in entries if (result := _item(row.get("name"), row.get("url"), row.get("snippet"), "bing"))]


def _brave(query: str, limit: int, timeout: int) -> list[dict[str, Any]]:
    key = os.getenv("BRAVE_SEARCH_API_KEY")
    if not key:
        return []
    url = "https://api.search.brave.com/res/v1/web/search?" + urlencode({"q": query, "count": limit})
    payload = _request_json(url, {"Accept": "application/json", "X-Subscription-Token": key}, timeout)
    entries = payload.get("web", {}).get("results", [])
    return [result for row in entries if (result := _item(row.get("title"), row.get("url"), row.get("description"), "brave"))]


def _gdelt(query: str, limit: int, timeout: int) -> list[dict[str, Any]]:
    url = "https://api.gdeltproject.org/api/v2/doc/doc?" + urlencode(
        {"query": query, "mode": "ArtList", "format": "json", "maxrecords": limit, "sort": "HybridRel"}
    )
    payload = _request_json(url, timeout=timeout)
    entries = payload.get("articles", [])
    return [result for row in entries if (result := _item(row.get("title"), row.get("url"), row.get("snippet"), "gdelt", row.get("seendate")))]


def _crossref(query: str, limit: int, timeout: int) -> list[dict[str, Any]]:
    url = "https://api.crossref.org/works?" + urlencode({"query.bibliographic": query, "rows": limit})
    payload = _request_json(url, timeout=timeout)
    entries = payload.get("message", {}).get("items", [])
    results = []
    for row in entries:
        titles = row.get("title") or []
        dates = row.get("published", {}).get("date-parts", [[]])
        published_at = "-".join(str(part) for part in dates[0]) if dates and dates[0] else None
        result = _item(titles[0] if titles else None, row.get("URL"), row.get("abstract"), "crossref", published_at)
        if result:
            results.append(result)
    return results


def _openalex(query: str, limit: int, timeout: int) -> list[dict[str, Any]]:
    url = "https://api.openalex.org/works?" + urlencode({"search": query, "per-page": limit})
    payload = _request_json(url, timeout=timeout)
    entries = payload.get("results", [])
    results = []
    for row in entries:
        location = row.get("primary_location") or {}
        landing_page = location.get("landing_page_url")
        result = _item(
            row.get("display_name"),
            landing_page or row.get("doi") or row.get("id"),
            None,
            "openalex",
            row.get("publication_date"),
        )
        if result:
            results.append(result)
    return results


_PROVIDERS = {
    "bing": ("web", "BING_SEARCH_KEY", _bing),
    "brave": ("web", "BRAVE_SEARCH_API_KEY", _brave),
    "gdelt": ("news", None, _gdelt),
    "crossref": ("academic", None, _crossref),
    "openalex": ("academic", None, _openalex),
}


def search_provider_health() -> dict[str, Any]:
    providers = {
        name: {
            "category": category,
            "access": "credential_required" if credential else "public",
            "status": "credential_missing" if credential and not os.getenv(credential) else "available_without_credentials",
            "credential_env": credential,
            "reachability": "not_probed",
        }
        for name, (category, credential, _) in _PROVIDERS.items()
    }
    return {
        "status": "ready",
        "providers": providers,
        "supported_categories": sorted({category for category, _, _ in _PROVIDERS.values()}),
        "limits": {"max_results_per_provider": 10, "max_timeout_seconds": 30},
    }


def multi_source_search(
    query: str,
    categories: list[str] | None = None,
    limit: int = DEFAULT_LIMIT,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    query = query.strip()
    selected_categories = set(categories or ("web", "news", "academic"))
    results: dict[str, list[dict[str, Any]]] = {
        "web": [],
        "news": [],
        "academic": [],
        "trade_databases": [],
        "patents": [],
    }
    source_status: dict[str, dict[str, str | None]] = {}

    if not query:
        return {"ok": False, "query": query, "results": results, "total_results": 0, "source_status": {}, "status": "invalid_query"}

    active: dict[str, tuple[str, Any]] = {}
    for name, (category, credential, search) in _PROVIDERS.items():
        if category not in selected_categories:
            continue
        if credential and not os.getenv(credential):
            source_status[name] = {"status": "not_configured", "credential_env": credential}
        else:
            active[name] = (category, search)

    with ThreadPoolExecutor(max_workers=max(1, len(active))) as executor:
        futures = {
            executor.submit(search, query, max(1, min(limit, 10)), max(1, min(timeout, 30))): (name, category)
            for name, (category, search) in active.items()
        }
        for future in as_completed(futures):
            name, category = futures[future]
            try:
                found = future.result()
                results[category].extend(found)
                source_status[name] = {"status": "ok", "credential_env": None}
            except Exception as error:
                source_status[name] = {"status": "error", "credential_env": None, "error": type(error).__name__}

    for category, items in results.items():
        unique: dict[str, dict[str, Any]] = {}
        for result in items:
            unique.setdefault(result["url"], result)
        results[category] = list(unique.values())

    successes = sum(item["status"] == "ok" for item in source_status.values())
    failures = sum(item["status"] == "error" for item in source_status.values())
    total_results = len({result["url"] for items in results.values() for result in items})
    if not active:
        status = "unavailable"
    elif failures or any(item["status"] == "not_configured" for item in source_status.values()):
        status = "partial" if successes else "unavailable"
    else:
        status = "complete"

    return {
        "ok": successes > 0,
        "query": query,
        "results": results,
        "total_results": total_results,
        "source_status": source_status,
        "status": status,
    }
