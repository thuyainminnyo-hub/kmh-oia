import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_assurance_package as validator


class AssurancePackageTests(unittest.TestCase):
    def test_checked_in_package_passes(self):
        self.assertEqual(validator.validate(), [])

    def test_gate_defaults_to_blocked(self):
        gate = validator.load("contracts/qa-gate.json")
        self.assertEqual(gate["default_decision"], "BLOCKED")
        self.assertFalse(gate["production_deployment_allowed"])

    def test_all_six_domains_are_present(self):
        scope = validator.load("contracts/scope-inventory.json")
        self.assertEqual({d["id"] for d in scope["domains"]}, validator.DOMAINS)

    def test_initial_status_does_not_claim_audit_pass(self):
        scope = validator.load("contracts/scope-inventory.json")
        self.assertTrue(all(d["status"] == "NOT_ASSESSED" for d in scope["domains"]))

    def test_approval_and_independent_review_are_not_fabricated(self):
        ledger = validator.load("artifacts/evidence-ledger.json")
        self.assertEqual(ledger["human_approval"]["status"], "NOT_GRANTED")
        self.assertEqual(ledger["independent_verification"]["status"], "NOT_RUN")

    def test_rejected_finding_requires_counter_evidence(self):
        finding = self.valid_finding(status="REJECTED_FALSE_POSITIVE")
        finding["counter_evidence"] = []
        errors = validator.validate_finding(finding, {"EV-001"})
        self.assertTrue(any("counter-evidence" in error for error in errors))

    def test_accepted_risk_requires_rationale(self):
        finding = self.valid_finding(status="ACCEPTED_RISK")
        errors = validator.validate_finding(finding, {"EV-001"})
        self.assertTrue(any("requires rationale" in error for error in errors))

    def test_unknown_evidence_reference_is_rejected(self):
        finding = self.valid_finding()
        finding["evidence_refs"] = ["EV-NOT-FOUND"]
        errors = validator.validate_finding(finding, {"EV-001"})
        self.assertTrue(any("unknown evidence" in error for error in errors))

    def test_verified_finding_requires_independent_reviewer(self):
        finding = self.valid_finding()
        finding["review"] = {"status": "VERIFIED", "independent_reviewer": ""}
        errors = validator.validate_finding(finding, {"EV-001"})
        self.assertTrue(any("independent reviewer" in error for error in errors))

    @staticmethod
    def valid_finding(status="CONFIRMED"):
        return {
            "finding_id": "KMEA-0001", "domain": "security", "title": "Synthetic test",
            "status": status, "severity": "LOW",
            "source": {"path": "src/security.py", "line_start": 1},
            "evidence_refs": ["EV-001"], "impact": "Synthetic impact",
            "recommendation": "Synthetic recommendation",
            "review": {"status": "NOT_REVIEWED", "independent_reviewer": ""}
        }


if __name__ == "__main__":
    unittest.main()
