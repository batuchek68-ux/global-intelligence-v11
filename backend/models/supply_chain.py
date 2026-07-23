from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Shipment:
    shipment_id: str = ""
    origin: str = ""
    destination: str = ""
    status: str = "pending"
    milestones: list = field(default_factory=list)


@dataclass
class QualityInspection:
    inspection_id: str = ""
    shipment_id: str = ""
    result: str = "pending"
    details: dict = field(default_factory=dict)
