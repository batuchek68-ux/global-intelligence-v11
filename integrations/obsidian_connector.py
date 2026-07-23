from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


KNOWLEDGE_ROOT = Path(__file__).resolve().parents[1] / "knowledge"


def _ensure_dirs() -> None:
    for sub in ["projects", "intelligence", "market", "risk", "templates", "connections", "daily", "archive"]:
        (KNOWLEDGE_ROOT / sub).mkdir(parents=True, exist_ok=True)


def _slug(text: str) -> str:
    allowed = []
    for ch in text.lower():
        if ch.isalnum():
            allowed.append(ch)
        elif ch in (" ", "-", "_"):
            allowed.append("-")
    slug = "".join(allowed).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "untitled"


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    if content.startswith("---"):
        end = content.find("---", 3)
        if end > 0:
            fm_text = content[3:end].strip()
            body = content[end + 3:].strip()
            fm = {}
            for line in fm_text.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip().strip('"').strip("'")
            return fm, body
    return {}, content


def read_note(relative_path: str) -> dict[str, Any]:
    path = KNOWLEDGE_ROOT / relative_path
    if not path.exists():
        return {"ok": False, "error": "Note not found", "path": relative_path}
    content = path.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(content)
    links = re.findall(r"\[\[([^\]]+)\]\]", content)
    tags = re.findall(r"#(\w+)", content)
    return {
        "ok": True,
        "path": relative_path,
        "frontmatter": frontmatter,
        "body": body,
        "content": content,
        "links": links,
        "tags": tags,
        "size": len(content),
        "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
    }


def write_note(relative_path: str, content: str, frontmatter: dict[str, Any] | None = None) -> dict[str, Any]:
    _ensure_dirs()
    path = KNOWLEDGE_ROOT / relative_path
    if frontmatter:
        fm_lines = ["---"]
        for k, v in frontmatter.items():
            fm_lines.append(f"{k}: {v}")
        fm_lines.append("---")
        full_content = "\n".join(fm_lines) + "\n\n" + content
    else:
        full_content = content
    path.write_text(full_content, encoding="utf-8")
    return {"ok": True, "path": relative_path, "size": len(full_content)}


def list_notes(subdirectory: str = "") -> dict[str, Any]:
    _ensure_dirs()
    base = KNOWLEDGE_ROOT / subdirectory if subdirectory else KNOWLEDGE_ROOT
    notes = []
    for f in sorted(base.rglob("*.md")):
        rel = f.relative_to(KNOWLEDGE_ROOT)
        content = f.read_text(encoding="utf-8")
        frontmatter, _ = _parse_frontmatter(content)
        links = re.findall(r"\[\[([^\]]+)\]\]", content)
        tags = re.findall(r"#(\w+)", content)
        notes.append({
            "path": str(rel),
            "title": frontmatter.get("title", f.stem),
            "tags": tags,
            "links": links,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        })
    return {"ok": True, "notes": notes, "count": len(notes)}


def search_notes(query: str, subdirectory: str = "") -> dict[str, Any]:
    _ensure_dirs()
    results = []
    base = KNOWLEDGE_ROOT / subdirectory if subdirectory else KNOWLEDGE_ROOT
    query_lower = query.lower()
    for f in sorted(base.rglob("*.md")):
        content = f.read_text(encoding="utf-8")
        if query_lower in content.lower():
            rel = f.relative_to(KNOWLEDGE_ROOT)
            frontmatter, _ = _parse_frontmatter(content)
            matches = [line.strip() for line in content.splitlines() if query_lower in line.lower()][:5]
            results.append({
                "path": str(rel),
                "title": frontmatter.get("title", f.stem),
                "matches": matches,
            })
    return {"ok": True, "query": query, "results": results, "count": len(results)}


def get_graph() -> dict[str, Any]:
    _ensure_dirs()
    nodes = []
    edges = []
    for f in KNOWLEDGE_ROOT.rglob("*.md"):
        rel = str(f.relative_to(KNOWLEDGE_ROOT))
        content = f.read_text(encoding="utf-8")
        frontmatter, _ = _parse_frontmatter(content)
        links = re.findall(r"\[\[([^\]]+)\]\]", content)
        tags = re.findall(r"#(\w+)", content)
        nodes.append({
            "id": rel,
            "title": frontmatter.get("title", f.stem),
            "tags": tags,
        })
        for link in links:
            target = _slug(link) + ".md"
            edges.append({"source": rel, "target": target, "label": "links_to"})
    return {"ok": True, "nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}


def create_daily_note(date_str: str | None = None) -> dict[str, Any]:
    _ensure_dirs()
    date_str = date_str or datetime.now().strftime("%Y-%m-%d")
    filename = f"daily/{date_str}.md"
    frontmatter = {
        "title": f"Daily Note: {date_str}",
        "date": date_str,
        "type": "daily",
        "created": datetime.now().isoformat(),
    }
    content = f"""## Market Intelligence

- 

## Project Updates

- 

## Risk Alerts

- 

## Key Decisions

- 

## Learning Notes

- 

## Links

- [[{date_str}]]
"""
    return write_note(filename, content, frontmatter)


def create_project_note(title: str, country: str = "", industry: str = "", details: dict[str, Any] | None = None) -> dict[str, Any]:
    _ensure_dirs()
    slug = _slug(title)
    filename = f"projects/{slug}.md"
    details = details or {}
    frontmatter = {
        "title": title,
        "country": country,
        "industry": industry,
        "type": "project",
        "status": details.get("status", "screening"),
        "created": datetime.now().isoformat(),
    }
    content = f"""## Overview

- **Country**: {country}
- **Industry**: {industry}
- **Status**: {details.get('status', 'screening')}

## Key Facts

- 

## Risk Assessment

- Level: 
- Score: /100
- Triggers: 

## Evidence

- 

## Decisions

- 

## Action Items

- [ ] 

## Connections

- 
"""
    return write_note(filename, content, frontmatter)


def create_intelligence_note(topic: str, region: str = "", source: str = "") -> dict[str, Any]:
    _ensure_dirs()
    slug = _slug(topic)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"intelligence/{date_str}-{slug}.md"
    frontmatter = {
        "title": f"Intelligence: {topic}",
        "region": region,
        "source": source,
        "type": "intelligence",
        "date": date_str,
        "created": datetime.now().isoformat(),
    }
    content = f"""## Topic

{topic}

## Region

{region}

## Source

{source}

## Key Findings

- 

## Evidence Chain

- 

## Confidence

- Level: 
- Notes: 

## Related Intelligence

- 

## Action Required

- [ ] 
"""
    return write_note(filename, content, frontmatter)


def create_risk_note(title: str, risk_level: str = "medium", category: str = "") -> dict[str, Any]:
    _ensure_dirs()
    slug = _slug(title)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"risk/{date_str}-{slug}.md"
    frontmatter = {
        "title": f"Risk: {title}",
        "risk_level": risk_level,
        "category": category,
        "type": "risk",
        "date": date_str,
        "created": datetime.now().isoformat(),
    }
    content = f"""## Risk Title

{title}

## Risk Level

{risk_level}

## Category

{category}

## Description

- 

## Impact

- 

## Mitigation

- 

## Evidence

- 

## Related Risks

- 

## Status

- [ ] Under review
- [ ] Mitigation plan created
- [ ] Resolved
"""
    return write_note(filename, content, frontmatter)


def create_connection_note(source: str, target: str, relationship: str = "", notes: str = "") -> dict[str, Any]:
    _ensure_dirs()
    slug = f"{_slug(source)}-to-{_slug(target)}"
    filename = f"connections/{slug}.md"
    frontmatter = {
        "title": f"{source} -> {target}",
        "source": source,
        "target": target,
        "relationship": relationship,
        "type": "connection",
        "created": datetime.now().isoformat(),
    }
    content = f"""## Connection

**{source}** --[[{relationship}]]--> **{target}**

## Details

{notes or "- "}

## Evidence

- 

## Confidence

- 
"""
    return write_note(filename, content, frontmatter)


def sync_project_to_knowledge(project_data: dict[str, Any]) -> dict[str, Any]:
    title = project_data.get("title", project_data.get("name", "Unknown Project"))
    result = create_project_note(
        title=title,
        country=project_data.get("country", ""),
        industry=project_data.get("industry", project_data.get("sector", "")),
        details=project_data,
    )
    return result


def sync_intelligence_to_knowledge(intel_data: dict[str, Any]) -> dict[str, Any]:
    topic = intel_data.get("topic", intel_data.get("query", "Unknown Topic"))
    result = create_intelligence_note(
        topic=topic,
        region=intel_data.get("country", intel_data.get("region", "")),
        source=intel_data.get("source", "system"),
    )
    return result


def sync_risk_to_knowledge(risk_data: dict[str, Any]) -> dict[str, Any]:
    title = risk_data.get("title", risk_data.get("project", "Unknown Risk"))
    result = create_risk_note(
        title=title,
        risk_level=risk_data.get("level", risk_data.get("risk_level", "medium")),
        category=risk_data.get("category", ""),
    )
    return result
