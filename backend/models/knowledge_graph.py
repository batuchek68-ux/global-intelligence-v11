from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class KGNode:
    node_id: str = ""
    label: str = ""
    properties: dict = field(default_factory=dict)


@dataclass
class KGRelationship:
    source: str = ""
    target: str = ""
    rel_type: str = ""
    properties: dict = field(default_factory=dict)
