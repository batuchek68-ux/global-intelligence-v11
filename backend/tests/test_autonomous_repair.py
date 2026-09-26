from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from workflows.autonomous_repair import BACKEND_ROOT, REPO_ROOT, compile_errors, validate_repair_payload
from workflows.persist_state import validated_source_files


class AutonomousRepairTests(unittest.TestCase):
    def test_compile_errors_reports_syntax_location(self) -> None:
        with tempfile.TemporaryDirectory(dir=BACKEND_ROOT) as directory:
            source = Path(directory) / "broken.py"
            source.write_text("def incomplete(\n", encoding="utf-8")

            errors = compile_errors([source])

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["path"], source.relative_to(REPO_ROOT).as_posix())
        self.assertIsNotNone(errors[0]["line"])

    def test_repair_payload_requires_exact_failed_file_set(self) -> None:
        expected = {"backend/core/broken.py"}
        response = json.dumps({"repairs": [{"path": "backend/core/broken.py", "content": "value = 1\n"}]})

        self.assertEqual(validate_repair_payload(response, expected), {"backend/core/broken.py": "value = 1\n"})

        unrelated = json.dumps({"repairs": [{"path": "backend/core/other.py", "content": "value = 1\n"}]})
        with self.assertRaises(ValueError):
            validate_repair_payload(unrelated, expected)

    def test_repair_payload_rejects_paths_outside_backend(self) -> None:
        response = json.dumps({"repairs": [{"path": "../README.md", "content": "changed\n"}]})

        with self.assertRaises(ValueError):
            validate_repair_payload(response, {"../README.md"})

    def test_persistence_only_accepts_successfully_repaired_backend_files(self) -> None:
        self.assertEqual(
            validated_source_files({"status": "repaired", "changed_files": ["backend/core/models.py"]}),
            ["backend/core/models.py"],
        )
        with self.assertRaises(ValueError):
            validated_source_files({"status": "manual_review_required", "changed_files": ["backend/core/models.py"]})
        with self.assertRaises(ValueError):
            validated_source_files({"status": "repaired", "changed_files": ["README.md"]})


if __name__ == "__main__":
    unittest.main()