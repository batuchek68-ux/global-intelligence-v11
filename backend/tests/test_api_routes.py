from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api import main


class JsonRequest:
    def __init__(self, body: object):
        self.body = body

    async def json(self) -> object:
        return self.body


class SearchApiTests(unittest.TestCase):
    def test_search_forwards_validated_options(self) -> None:
        expected = {"ok": True, "status": "complete"}
        with patch.object(main, "_require_core_allowed"):
            with patch.object(main, "multi_source_search", return_value=expected) as search:
                result = asyncio.run(main.search(JsonRequest({
                    "query": "  port logistics  ",
                    "categories": ["web", "academic"],
                    "limit": 3,
                    "timeout_seconds": 4,
                })))

        self.assertEqual(result, expected)
        search.assert_called_once_with("port logistics", categories=["web", "academic"], limit=3, timeout=4)

    def test_search_rejects_unimplemented_sources_before_search(self) -> None:
        with patch.object(main, "_require_core_allowed"):
            with patch.object(main, "multi_source_search") as search:
                with self.assertRaises(HTTPException) as raised:
                    asyncio.run(main.search(JsonRequest({"query": "port", "categories": ["patents"]})))

        self.assertEqual(raised.exception.status_code, 422)
        search.assert_not_called()

    def test_capabilities_and_critical_routes_are_available(self) -> None:
        with patch.object(main, "_require_core_allowed"):
            capabilities = asyncio.run(main.system_capabilities())

        self.assertIn("agents", capabilities)
        self.assertIn("search", capabilities)
        self.assertIn("self_improvement", capabilities)
        self.assertEqual(main.N8NConnector.__module__, "integrations.n8n_connector")
        paths = main.app.openapi()["paths"]
        self.assertIn("/v1/search", paths)
        self.assertIn("/v1/system/capabilities", paths)


if __name__ == "__main__":
    unittest.main()