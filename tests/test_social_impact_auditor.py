import unittest

from src.social_impact_auditor import (
    AuditChain, EvidenceItem, EvidenceStatus, PlatformCase,
    PlatformTransparencyAuditor, ReviewDisposition,
)


class PlatformTransparencyAuditorTests(unittest.TestCase):
    def test_no_verified_evidence_requires_more_evidence(self):
        case = PlatformCase("SII-CASE-001", "withdrawal_dispute", (
            EvidenceItem("EV-1", "screenshot", EvidenceStatus.PENDING,
                         ("additional_payment_requested_after_withdrawal",)),
        ))
        result = PlatformTransparencyAuditor().evaluate(case)
        self.assertEqual(result.disposition, ReviewDisposition.MORE_EVIDENCE_REQUIRED)
        self.assertEqual(result.signals, ())

    def test_verified_observation_emits_review_signal_not_fraud_finding(self):
        case = PlatformCase("SII-CASE-002", "withdrawal_dispute", (
            EvidenceItem("EV-2", "message_export", EvidenceStatus.VERIFIED,
                         ("additional_payment_requested_after_withdrawal",)),
        ))
        result = PlatformTransparencyAuditor().evaluate(case)
        self.assertEqual(result.disposition, ReviewDisposition.HUMAN_REVIEW_RECOMMENDED)
        self.assertEqual(result.signals[0].code, "additional_payment_before_withdrawal")
        self.assertIn("EV-2", result.signals[0].supporting_evidence_ids)
        self.assertNotIn("fraud", result.disposition.value)

    def test_pending_and_rejected_evidence_do_not_trigger_rules(self):
        case = PlatformCase("SII-CASE-003", "account_restriction", (
            EvidenceItem("EV-3", "screenshot", EvidenceStatus.PENDING,
                         ("account_restricted_without_reason",)),
            EvidenceItem("EV-4", "note", EvidenceStatus.REJECTED,
                         ("account_restricted_without_reason",)),
        ))
        result = PlatformTransparencyAuditor().evaluate(case)
        self.assertEqual(result.disposition, ReviewDisposition.MORE_EVIDENCE_REQUIRED)
        self.assertEqual(result.rejected_evidence_count, 1)
        self.assertEqual(result.unverified_evidence_count, 1)

    def test_duplicate_evidence_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            PlatformCase("SII-CASE-004", "withdrawal_dispute", (
                EvidenceItem("EV-X", "receipt", EvidenceStatus.PENDING),
                EvidenceItem("EV-X", "message", EvidenceStatus.PENDING),
            ))

    def test_invalid_sha256_is_rejected(self):
        with self.assertRaises(ValueError):
            EvidenceItem("EV-5", "receipt", EvidenceStatus.VERIFIED, content_sha256="not-a-hash")

    def test_audit_chain_detects_mutation(self):
        chain = AuditChain()
        auditor = PlatformTransparencyAuditor(chain)
        auditor.evaluate(PlatformCase("SII-CASE-006", "withdrawal_dispute", (
            EvidenceItem("EV-6", "receipt", EvidenceStatus.VERIFIED,
                         ("withdrawal_delayed_without_timeline",)),
        )))
        self.assertTrue(chain.verify())
        chain.events[0].details["disposition"] = "tampered"
        self.assertFalse(chain.verify())


if __name__ == "__main__":
    unittest.main()
