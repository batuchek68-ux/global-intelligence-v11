from __future__ import annotations


_LICENSE = {"tier": "community", "active": True, "features": ["core", "agents", "orchestration"]}


def core_allowed() -> bool:
    return _LICENSE.get("active", False)


def license_status() -> dict:
    return {"license": _LICENSE}
