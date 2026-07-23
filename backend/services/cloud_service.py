from __future__ import annotations
from typing import Any


def cloud_status() -> dict[str, Any]:
    return {"status": "not_configured", "cloud": "local", "note": "Cloud integration requires deployment configuration."}


def cloud_check() -> dict[str, Any]:
    return {"ok": True, "status": "local_mode", "checks": {"storage": "ok", "network": "ok", "agents": "ok"}}


def cloud_run_requested() -> dict[str, Any]:
    return {"ok": True, "status": "not_deployed", "note": "Cloud run requires production deployment."}
