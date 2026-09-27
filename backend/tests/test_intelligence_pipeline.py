from __future__ import annotations

import json
import asyncio
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services import search_service, self_improvement_service
from backend.services.due_diligence_service import SANCTIONS_JURISDICTIONS, screen_sanctions, verify_counterparty
from backend.workflows import system_integrity
from core.agents import (
    AgentPool,
    CounterpartyVerificationAgent,
    EvidencePlannerAgent,
    EvidenceQualityAgent,
    RiskGateAgent,
    SanctionsScreeningAgent,
    SearchResearchAgent,
)
from core.orchestration import OrchestrationEngine


SANCTIONS_SOURCE_URLS = {
    "OFAC": "https://ofac.treasury.gov/list.xml",
    "UN": "https://scsanctions.un.org/list.xml",
    "EU": "https://data.europa.eu/list.xml",
    "UK": "https://www.gov.uk/list.xml",
}


class JsonResponse:
    def __init__(self, payload: dict):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "JsonResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


class SearchServiceTests(unittest.TestCase):
    def test_queries_configured_web_providers_and_keeps_partial_results(self) -> None:
        def fake_urlopen(request, timeout):
            host = urlparse(request.full_url).netloc
            if host == "api.search.brave.com":
                raise HTTPError(request.full_url, 503, "unavailable", {}, None)
            return JsonResponse({"webPages": {"value": [{"name": "Official source", "url": "https://example.gov/page", "snippet": "Evidence"}]}})

        with patch.dict("os.environ", {"BING_SEARCH_KEY": "test-key", "BRAVE_SEARCH_API_KEY": "test-key"}):
            with patch.object(search_service, "urlopen", side_effect=fake_urlopen):
                result = search_service.multi_source_search("infrastructure project", ["web"])

        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["total_results"], 1)
        self.assertEqual(result["source_status"]["bing"]["status"], "ok")
        self.assertEqual(result["source_status"]["brave"]["status"], "error")
        self.assertEqual(result["source_status"]["brave"]["error"], "HTTPError")

    def test_missing_web_credentials_degrades_without_network_calls(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with patch.object(search_service, "urlopen") as mocked_urlopen:
                result = search_service.multi_source_search("infrastructure project", ["web"])

        mocked_urlopen.assert_not_called()
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["source_status"]["bing"]["status"], "not_configured")

    def test_provider_health_does_not_claim_unprobed_network_reachability(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            health = search_service.search_provider_health()

        self.assertEqual(health["providers"]["bing"]["status"], "credential_missing")
        self.assertEqual(health["providers"]["crossref"]["access"], "public")
        self.assertEqual(health["providers"]["crossref"]["reachability"], "not_probed")


class IntelligencePipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_parallel_research_agents_feed_synthesis_and_quality_gate(self) -> None:
        pool = AgentPool()
        engine = OrchestrationEngine({})
        for name, agent in pool.get_all_agents().items():
            engine.register_agent(name, agent)

        search_queries = []

        def fake_search(query: str, categories: list[str]) -> dict:
            search_queries.append((categories[0], query))
            category = categories[0]
            provider = {"web": "bing", "news": "gdelt", "academic": "crossref"}[category]
            return {
                "ok": True,
                "query": query,
                "results": {category: [{"title": category, "url": f"https://example.test/{category}", "source": provider}]},
                "total_results": 1,
                "source_status": {provider: {"status": "ok", "credential_env": None}},
                "status": "complete",
            }

        with patch("core.agents.multi_source_search", side_effect=fake_search):
            with patch("core.orchestration.append_audit"):
                with patch("core.orchestration.record_execution_outcome"):
                    result = await engine.execute_query("Kazakhstan logistics project", "test-org", "test-user")

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["task_count"], 14)
        self.assertIn("sanctions_screening", pool.health_check()["contracts"])
        synthesized = result["result"]
        self.assertEqual(set(synthesized["evidence_results"]), {"web", "news", "academic"})
        self.assertEqual(synthesized["evidence_quality"]["evidence_count"], 3)
        self.assertFalse(synthesized["risk_gate"]["evidence_review_required"])
        self.assertEqual(synthesized["sanctions_screening"]["status"], "skipped")
        self.assertEqual(synthesized["counterparty_verification"]["status"], "skipped")
        self.assertTrue(any(category == "news" and "project news" in query for category, query in search_queries))

    async def test_named_counterparty_flows_through_due_diligence_and_human_gate(self) -> None:
        pool = AgentPool()
        engine = OrchestrationEngine({})
        for name, agent in pool.get_all_agents().items():
            engine.register_agent(name, agent)

        def fake_search(query: str, categories: list[str]) -> dict:
            category = categories[0]
            provider = {"web": "bing", "news": "gdelt", "academic": "crossref"}[category]
            return {
                "ok": True,
                "query": query,
                "results": {category: []},
                "total_results": 0,
                "source_status": {provider: {"status": "ok", "credential_env": None}},
                "status": "complete",
            }

        with patch("core.agents.multi_source_search", side_effect=fake_search):
            with patch("core.orchestration.append_audit"):
                with patch("core.orchestration.record_execution_outcome"):
                    result = await engine.execute_query(
                        "Review cross-border transaction",
                        "test-org",
                        "test-user",
                        metadata={"counterparties": [{"name": "Example Trading LLC", "country": "Kazakhstan"}]},
                    )

        self.assertEqual(result["status"], "success")
        academic_task = next(task for task in result["tasks"] if task["agent_type"] == "academic_researcher")
        self.assertEqual(academic_task["status"], "skipped")
        response = result["result"]
        self.assertEqual(response["sanctions_screening"]["status"], "inconclusive")
        self.assertEqual(response["counterparty_verification"]["status"], "unavailable")
        self.assertTrue(response["risk_gate"]["needs_human_approval"])
        self.assertEqual(response["decision"]["decision"], "blocked_pending_human_approval")


class SelfImprovementTests(unittest.TestCase):
    def test_execution_feedback_drives_measured_cycle_recommendations(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            state_file = Path(directory) / "self_improvement.json"
            with unittest.mock.patch.object(self_improvement_service, "STATE_FILE", state_file):
                self_improvement_service.record_execution_outcome({
                    "evidence_quality": {
                        "quality_score": 0.4,
                        "provider_status": {
                            "bing": {"status": "error", "credential_env": "BING_SEARCH_KEY"}
                        },
                    }
                })

                plan = self_improvement_service.build_self_improvement_plan()
                cycle = self_improvement_service.run_self_improvement_cycle()

        self.assertEqual(plan["areas"][2]["current_score"], 0.4)
        self.assertTrue(any("BING_SEARCH_KEY" in item for item in plan["recommendations"]))
        self.assertEqual(cycle["status"], "recommendations_generated")

    def test_integrity_check_repairs_only_required_repository_directories(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = system_integrity.run_integrity_check(auto_fix=True, project_root=root)

            self.assertTrue(result["ok"])
            self.assertEqual(set(result["checks"]["directories"]), {"memory", "reports", "projects", "comm"})
            self.assertTrue(all((root / name).is_dir() for name in result["checks"]["directories"]))


class DueDiligenceTests(unittest.TestCase):
    def test_due_diligence_search_targets_party_and_skips_irrelevant_academic_sources(self) -> None:
        metadata = {
            "counterparties": [{
                "name": "Example Trading LLC",
                "aliases": ["Example Trading"],
                "country": "Indonesia",
            }],
            "sanctions_screening_required": True,
        }

        async def run_agents() -> tuple[dict, dict, dict]:
            planner = await EvidencePlannerAgent().execute_async(
                {"query": "check counterparty", "metadata": metadata, "prev_task_2": {}},
                "test-org",
            )
            academic = await SearchResearchAgent("academic").execute_async(
                {"query": "check counterparty", "metadata": metadata, "prev_task_3": planner},
                "test-org",
            )
            quality = await EvidenceQualityAgent().execute_async({
                "prev_task_4": {"category": "web", "total_results": 0, "source_status": {"bing": {"status": "not_configured"}}},
                "prev_task_5": {"category": "news", "total_results": 0, "source_status": {"gdelt": {"status": "error"}}},
                "prev_task_6": academic,
            }, "test-org")
            return planner, academic, quality

        planner, academic, quality = asyncio.run(run_agents())

        self.assertIn("Example Trading LLC", planner["search_queries_by_category"]["web"])
        self.assertIn("Example Trading", planner["search_queries_by_category"]["news"])
        self.assertIn("Indonesia", planner["search_queries_by_category"]["web"])
        self.assertNotIn("Kazakhstan", planner["search_queries_by_category"]["web"])
        self.assertEqual(academic["status"], "skipped")
        self.assertEqual(academic["total_results"], 0)
        self.assertEqual(quality["quality_score"], 0)
        self.assertTrue(quality["review_required"])

    def test_unresolved_due_diligence_blocks_automatic_approval(self) -> None:
        async def run_agents() -> dict:
            request = {
                "metadata": {"counterparties": [{"name": "Example Trading LLC", "country": "Kazakhstan"}]},
                "prev_task_2": {"risk_terms": []},
            }
            sanctions = await SanctionsScreeningAgent().execute_async(request, "test-org")
            counterparty = await CounterpartyVerificationAgent().execute_async(request, "test-org")
            gate = await RiskGateAgent().execute_async({
                **request,
                "prev_task_3": {"required_sources": []},
                "prev_task_7": {"quality_score": 1.0},
                "prev_task_13": sanctions,
                "prev_task_14": counterparty,
            }, "test-org")
            return {"sanctions": sanctions, "counterparty": counterparty, "gate": gate}

        result = asyncio.run(run_agents())

        self.assertEqual(result["sanctions"]["status"], "inconclusive")
        self.assertEqual(result["counterparty"]["status"], "unavailable")
        self.assertTrue(result["gate"]["needs_human_approval"])
        self.assertTrue(result["gate"]["due_diligence_review_required"])

    def test_sanctions_screening_is_inconclusive_when_any_list_is_unavailable(self) -> None:
        source_results = {
            "UN": {
                "status": "available",
                "records": [],
                "source_url": "https://example.un.test/list.xml",
                "updated_at": "2026-09-26",
            }
        }

        result = screen_sanctions({"name": "Example Trading LLC"}, source_results)

        self.assertEqual(result["screening_status"], "inconclusive")
        self.assertFalse(result["coverage_complete"])

    def test_complete_source_coverage_can_return_limited_no_match_result(self) -> None:
        source_results = {
            jurisdiction: {
                "status": "available",
                "records": [{"names": ["Different Entity"]}],
                "source_url": SANCTIONS_SOURCE_URLS[jurisdiction],
                "updated_at": "2026-09-26",
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            for jurisdiction in SANCTIONS_JURISDICTIONS
        }

        result = screen_sanctions({"name": "Example Trading LLC"}, source_results)

        self.assertEqual(result["screening_status"], "no_match_found")
        self.assertTrue(result["coverage_complete"])

    def test_non_official_or_stale_sanctions_source_cannot_clear_screening(self) -> None:
        checked_at = datetime.now(timezone.utc).isoformat()
        source_results = {
            jurisdiction: {
                "status": "available",
                "records": [{"names": ["Different Entity"]}],
                "source_url": SANCTIONS_SOURCE_URLS[jurisdiction],
                "updated_at": "2026-09-26",
                "checked_at": checked_at,
            }
            for jurisdiction in SANCTIONS_JURISDICTIONS
        }
        source_results["EU"]["source_url"] = "https://not-eu.example/list.xml"
        source_results["UK"]["checked_at"] = "2020-01-01T00:00:00+00:00"

        result = screen_sanctions({"name": "Example Trading LLC"}, source_results)

        self.assertEqual(result["screening_status"], "inconclusive")
        self.assertEqual(result["source_status"]["EU"]["status"], "unavailable")
        self.assertEqual(result["source_status"]["UK"]["status"], "unavailable")

    def test_malformed_date_or_nameless_records_cannot_clear_screening(self) -> None:
        source_results = {
            jurisdiction: {
                "status": "available",
                "records": [{"names": ["Different Entity"]}],
                "source_url": SANCTIONS_SOURCE_URLS[jurisdiction],
                "updated_at": "2026-09-26",
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            for jurisdiction in SANCTIONS_JURISDICTIONS
        }
        source_results["EU"]["updated_at"] = "2026-09-26-not-a-date"
        source_results["UK"]["records"] = [{"names": [""]}]

        result = screen_sanctions({"name": "Example Trading LLC"}, source_results)

        self.assertEqual(result["screening_status"], "inconclusive")
        self.assertEqual(result["source_status"]["EU"]["status"], "unavailable")
        self.assertEqual(result["source_status"]["UK"]["status"], "unavailable")

    def test_sanctions_exact_alias_match_is_a_potential_match(self) -> None:
        source_results = {
            jurisdiction: {
                "status": "available",
                "records": [{"names": ["Example & Sons LLC"], "list_id": "TEST-1"}],
                "source_url": SANCTIONS_SOURCE_URLS[jurisdiction],
                "updated_at": "2026-09-26",
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
            for jurisdiction in SANCTIONS_JURISDICTIONS
        }

        result = screen_sanctions({"name": "Example and Sons, LLC"}, source_results)

        self.assertEqual(result["screening_status"], "potential_match")
        self.assertEqual(len(result["matches"]), 4)

    def test_counterparty_without_official_registry_adapter_is_unavailable(self) -> None:
        result = verify_counterparty({"name": "Example Trading LLC", "country": "Kazakhstan"})

        self.assertEqual(result["identity_status"], "unavailable")
        self.assertIsNone(result["registry_source"])

    def test_counterparty_registry_result_must_match_submitted_identity(self) -> None:
        entity = {"name": "Example Trading LLC", "country": "Kazakhstan"}
        registry_result = {
            "legal_name": "Different Trading LLC",
            "country": "Kazakhstan",
            "registration_number": "KZ-123",
            "registry_source": "Official registry",
            "source_url": "https://registry.gov.kz/company/KZ-123",
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        result = verify_counterparty(entity, registry_result)

        self.assertEqual(result["identity_status"], "conflicting")

    def test_counterparty_registry_result_verifies_matching_legal_name(self) -> None:
        entity = {"name": "Example Trading, LLC", "country": "Kazakhstan"}
        registry_result = {
            "legal_name": "Example Trading LLC",
            "country": "Kazakhstan",
            "registration_number": "KZ-123",
            "registry_source": "Official registry",
            "source_url": "https://registry.gov.kz/company/KZ-123",
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        result = verify_counterparty(entity, registry_result)

        self.assertEqual(result["identity_status"], "verified")
        self.assertEqual(result["matched_on"], "legal_name")

    def test_counterparty_registration_and_country_conflicts_are_not_downgraded(self) -> None:
        registry_result = {
            "legal_name": "Example Trading LLC",
            "country": "Indonesia",
            "registration_number": "ID-456",
            "registry_source": "Official registry",
            "source_url": "https://registry.gov.id/company/ID-456",
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        country_conflict = verify_counterparty({
            "name": "Example Trading LLC",
            "country": "Kazakhstan",
            "registration_number": "ID-456",
        }, registry_result)
        registration_conflict = verify_counterparty({
            "name": "Example Trading LLC",
            "country": "Indonesia",
            "registration_number": "ID-999",
        }, registry_result)

        self.assertEqual(country_conflict["identity_status"], "conflicting")
        self.assertEqual(registration_conflict["identity_status"], "conflicting")

    def test_stale_registry_lookup_cannot_verify_counterparty(self) -> None:
        result = verify_counterparty(
            {"name": "Example Trading LLC", "country": "Kazakhstan"},
            {
                "legal_name": "Example Trading LLC",
                "country": "Kazakhstan",
                "registration_number": "KZ-123",
                "registry_source": "Official registry",
                "source_url": "https://registry.gov.kz/company/KZ-123",
                "checked_at": "2020-01-01T00:00:00+00:00",
            },
        )

        self.assertEqual(result["identity_status"], "partial")


if __name__ == "__main__":
    unittest.main()