"""Remediation branch smoke test for the core intelligence package."""

import unittest

from backend.services.due_diligence_service import screen_sanctions, verify_counterparty


class DueDiligenceRemediationTests(unittest.TestCase):
    def test_sanctions_screen_is_safe_and_explicit(self):
        result = screen_sanctions("Example Trading LLC", ["Example Trading"])
        self.assertEqual(result["status"], "inconclusive")
        self.assertEqual(result["matches"], [])

    def test_counterparty_verification_is_not_claimed(self):
        result = verify_counterparty("Example Trading LLC", {"country": "Kazakhstan"})
        self.assertEqual(result["status"], "unavailable")
        self.assertFalse(result["verifications"])

    def test_missing_names_are_rejected(self):
        with self.assertRaises(ValueError):
            screen_sanctions("")
        with self.assertRaises(ValueError):
            verify_counterparty("  ")


if __name__ == "__main__":
    unittest.main()
