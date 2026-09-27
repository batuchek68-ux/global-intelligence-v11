from __future__ import annotations

import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services import due_diligence_learning_service as learning
from backend.workflows import run_due_diligence
from backend.workflows.run_due_diligence import validate_request


class DueDiligenceRunnerTests(unittest.TestCase):
    def test_request_validation_normalizes_counterparty_metadata(self) -> None:
        request = validate_request({
            "query": "  Review a transaction  ",
            "metadata": {
                "counterparties": {
                    "name": "Example Trading LLC",
                    "aliases": [" Example Trading "],
                    "country": "Kazakhstan",
                    "registration_number": "KZ-123",
                },
                "sanctions_screening_required": True,
            },
        })

        self.assertEqual(request["query"], "Review a transaction")
        self.assertEqual(request["metadata"]["counterparties"][0]["aliases"], ["Example Trading"])
        self.assertTrue(request["metadata"]["sanctions_screening_required"])

    def test_request_validation_rejects_invalid_party_and_oversized_inputs(self) -> None:
        with self.assertRaises(ValueError):
            validate_request({"query": "review", "metadata": {"counterparties": [{"name": " "}]}})
        with self.assertRaises(ValueError):
            validate_request({"query": "x" * 3001})
        with self.assertRaises(ValueError):
            validate_request({"query": "review", "metadata": {"sanctions_screening_required": "yes"}})

    def test_learning_memory_aggregates_statuses_without_party_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            memory_dir = Path(directory)
            with patch.object(learning, "MEMORY_DIR", memory_dir):
                with patch.object(learning, "RUN_LOG", memory_dir / "runs.jsonl"):
                    with patch.object(learning, "LEARNING_STATE", memory_dir / "learning.json"):
                        summary = learning.record_due_diligence_outcome({
                            "sanctions_screening": {
                                "status": "inconclusive",
                                "screenings": [{
                                    "entity_name": "Sensitive Counterparty Ltd",
                                    "source_status": {
                                        "OFAC": {"status": "unavailable"},
                                        "UN": {"status": "available"},
                                    },
                                }],
                            },
                            "counterparty_verification": {
                                "status": "unavailable",
                                "verifications": [{"entity_name": "Sensitive Counterparty Ltd"}],
                            },
                            "risk_gate": {"needs_human_approval": True},
                        })
                        log = (memory_dir / "runs.jsonl").read_text(encoding="utf-8")
                        state = json.loads((memory_dir / "learning.json").read_text(encoding="utf-8"))

        self.assertEqual(summary["run_count"], 1)
        self.assertEqual(state["sanctions_status_counts"], {"inconclusive": 1})
        self.assertEqual(state["sanctions_source_status_counts"]["OFAC"], {"unavailable": 1})
        self.assertNotIn("Sensitive Counterparty Ltd", log)
        self.assertIn("authoritative sanctions-list adapters", " ".join(summary["recommendations"]))

    def test_failed_run_memory_is_anonymous_and_recovers_corrupt_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            memory_dir = Path(directory)
            log_path = memory_dir / "runs.jsonl"
            state_path = memory_dir / "learning.json"
            state_path.write_text("[]", encoding="utf-8")
            with patch.object(learning, "MEMORY_DIR", memory_dir):
                with patch.object(learning, "RUN_LOG", log_path):
                    with patch.object(learning, "LEARNING_STATE", state_path):
                        summary = learning.record_due_diligence_failure("request_validation", "ValueError")
            observation = json.loads(log_path.read_text(encoding="utf-8"))
            state = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(summary, {"run_count": 1, "failed_run_count": 1})
        self.assertEqual(observation["error_type"], "ValueError")
        self.assertNotIn("message", observation)
        self.assertEqual(state["human_review_count"], 0)

    def test_runner_writes_report_and_learning_without_network_calls(self) -> None:
        async def fake_execute(request: dict) -> dict:
            return {
                "status": "success",
                "execution_id": "exec-test",
                "task_count": 14,
                "tasks": [{"agent_type": "sanctions_screening", "name": "sanctions_screening", "status": "completed"}],
                "result": {
                    "sanctions_screening": {"status": "inconclusive", "screenings": []},
                    "counterparty_verification": {"status": "unavailable", "verifications": []},
                    "risk_gate": {"needs_human_approval": True},
                    "decision": {"decision": "blocked_pending_human_approval", "action_plan": []},
                    "evidence_quality": {
                        "provider_status": {"bing": {"status": "not_configured", "credential_env": "BING_SEARCH_KEY"}},
                    },
                    "evidence_results": {
                        "web": [{"title": "Official registry result", "url": "https://registry.example.test/entity"}],
                        "news": [],
                        "academic": [],
                    },
                },
            }

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(run_due_diligence, "REPORT_DIR", root / "reports"):
                with patch.object(learning, "MEMORY_DIR", root / "memory"):
                    with patch.object(learning, "RUN_LOG", root / "memory" / "runs.jsonl"):
                        with patch.object(learning, "LEARNING_STATE", root / "memory" / "learning.json"):
                            with patch.object(run_due_diligence, "_execute", side_effect=fake_execute):
                                with patch.object(sys, "argv", ["run_due_diligence.py"]):
                                    with patch.dict("os.environ", {
                                        "DUE_DILIGENCE_REQUEST_JSON": json.dumps({
                                            "query": "Check Example Trading LLC",
                                            "metadata": {"counterparties": [{"name": "Example Trading LLC"}]},
                                        }),
                                        "GITHUB_RUN_ID": "test-123",
                                    }):
                                        with redirect_stdout(StringIO()):
                                            with redirect_stderr(StringIO()):
                                                exit_code = run_due_diligence.main()
            report = json.loads((root / "reports" / "due_diligence_test-123.json").read_text(encoding="utf-8"))
            markdown = (root / "reports" / "due_diligence_test-123.md").read_text(encoding="utf-8")
            learning_state = json.loads((root / "memory" / "learning.json").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["result"]["decision"]["decision"], "blocked_pending_human_approval")
        self.assertEqual(learning_state["run_count"], 1)
        self.assertIn("## Modules", markdown)
        self.assertIn("BING_SEARCH_KEY", markdown)
        self.assertIn("Official registry result", markdown)
        self.assertIn("1 result(s)", markdown)


if __name__ == "__main__":
    unittest.main()