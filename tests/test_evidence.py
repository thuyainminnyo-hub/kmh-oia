import hashlib
import unittest

from src.evidence import (
    Claim, ClaimVerifier, EvidenceKnowledgeSource, EvidenceRecord, EvidenceRegistry,
)


class EvidenceAwareKnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.registry = EvidenceRegistry()
        self.record = EvidenceRecord.create(
            evidence_id="ev-001",
            source_id="doc-001",
            source_uri="https://example.invalid/policy",
            locator="section-2",
            content="KMH OIA uses governed tools and structured traces.",
            owner="pilot-owner",
            captured_at="2026-11-02T00:00:00+00:00",
        )
        self.registry.add_candidate(self.record)

    def test_candidate_is_not_retrievable_before_activation(self):
        source = EvidenceKnowledgeSource(self.registry)
        self.assertEqual(source.retrieve("KMH OIA"), [])

    def test_valid_record_can_be_activated_and_retrieved_with_citation(self):
        result = self.registry.activate("ev-001")
        self.assertTrue(result.accepted)
        items = EvidenceKnowledgeSource(self.registry).retrieve("KMH")
        self.assertEqual(len(items), 1)
        self.assertIn("evidence:ev-001", items[0].source)
        self.assertIn("sha256:", items[0].source)

    def test_claim_fails_until_evidence_is_active(self):
        verifier = ClaimVerifier(self.registry)
        result = verifier.verify(Claim("claim-1", "KMH uses governed tools", ("ev-001",)))
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "evidence_not_active")

    def test_claim_passes_with_active_valid_evidence(self):
        self.registry.activate("ev-001")
        result = ClaimVerifier(self.registry).verify(
            Claim("claim-1", "KMH uses governed tools", ("ev-001",))
        )
        self.assertTrue(result.accepted)
        self.assertEqual(result.reason, "verified")
        self.assertEqual(len(result.citations), 1)

    def test_missing_evidence_fails_closed(self):
        result = ClaimVerifier(self.registry).verify(
            Claim("claim-2", "Unsupported claim", ("missing",))
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "evidence_not_active")

    def test_hash_tampering_is_rejected(self):
        tampered = EvidenceRecord(
            **{**self.record.__dict__, "content": "tampered content"}
        )
        registry = EvidenceRegistry()
        registry.add_candidate(tampered)
        result = registry.activate("ev-001")
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "content_hash_mismatch")

    def test_incomplete_provenance_is_rejected(self):
        bad = EvidenceRecord.create(
            "ev-bad", "doc-bad", "", "line-1", "some content", owner="pilot-owner"
        )
        registry = EvidenceRegistry()
        registry.add_candidate(bad)
        result = registry.activate("ev-bad")
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "provenance_incomplete")

    def test_minimum_evidence_gate(self):
        self.registry.activate("ev-001")
        result = ClaimVerifier(self.registry, minimum_evidence=2).verify(
            Claim("claim-3", "Needs corroboration", ("ev-001",))
        )
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "insufficient_evidence")


if __name__ == "__main__":
    unittest.main()
