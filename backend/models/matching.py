from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MatchResult:
    buyer_id: str = ""
    supplier_id: str = ""
    score: float = 0.0
    match_details: dict = field(default_factory=dict)


@dataclass
class MatchRequest:
    query: str = ""
    industry: str = ""
    country: str = ""
    requirements: dict = field(default_factory=dict)
