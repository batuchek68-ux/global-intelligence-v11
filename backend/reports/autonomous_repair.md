# Autonomous Repair Report

- Generated: 2026-09-26T13:16:55+00:00 UTC
- Status: tests_failed
- Repair necessary: true

## Compilation

- No initial backend Python compile errors detected.
- All backend Python files compile successfully after diagnosis.

## Repair

- No source changes were necessary.

## Tests

- Available: true
- Passed: false

```text
test_compile_errors_reports_syntax_location (test_autonomous_repair.AutonomousRepairTests.test_compile_errors_reports_syntax_location) ... ok
test_persistence_only_accepts_successfully_repaired_backend_files (test_autonomous_repair.AutonomousRepairTests.test_persistence_only_accepts_successfully_repaired_backend_files) ... ERROR
test_repair_payload_rejects_paths_outside_backend (test_autonomous_repair.AutonomousRepairTests.test_repair_payload_rejects_paths_outside_backend) ... ok
test_repair_payload_requires_exact_failed_file_set (test_autonomous_repair.AutonomousRepairTests.test_repair_payload_requires_exact_failed_file_set) ... ok

======================================================================
ERROR: test_persistence_only_accepts_successfully_repaired_backend_files (test_autonomous_repair.AutonomousRepairTests.test_persistence_only_accepts_successfully_repaired_backend_files)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "F:\Documents\GitHub\global-intelligence-v11\backend\tests\test_autonomous_repair.py", line 42, in test_persistence_only_accepts_successfully_repaired_backend_files
    validated_source_files({"status": "repaired", "changed_files": ["backend/core/models.py"]}),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\Documents\GitHub\global-intelligence-v11\backend\workflows\persist_state.py", line 41, in validated_source_files
    raise ValueError(f"Repair report contains an unsafe or missing source path: {path}")
ValueError: Repair report contains an unsafe or missing source path: backend/core/models.py

----------------------------------------------------------------------
Ran 4 tests in 0.126s

FAILED (errors=1)

```

## Notes

- Tests failed; no automated behavioral repair was attempted.
- Human review is required: fix the failing test suite before release or publishing.
