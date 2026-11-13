import unittest

from src.laphet_pilot import assess_publication_readiness


def ready_record():
    artifact_sha = "a" * 64
    return {
        "record_id": "KMH-LAPHET-001",
        "record_version": "0.1.0",
        "record_status": "APPROVED_FOR_PUBLICATION",
        "access_classification": "PUBLIC",
        "attribution_mode": "COMMUNITY_ONLY",
        "consent": {
            "status": "ACTIVE",
            "scopes": {
                "documentation": True,
                "attribution": False,
                "public_publication": True,
                "translation": True,
                "commercial_reuse": False,
            },
            "evidence_ids": ["CONSENT-001"],
        },
        "evidence": [
            {
                "id": "CONSENT-001",
                "evidence_type": "consent_record",
                "access_classification": "RESTRICTED",
                "publication_permission": False,
            },
            {
                "id": "SRC-001",
                "evidence_type": "public_research",
                "access_classification": "PUBLIC",
                "publication_permission": True,
                "source_uri": "https://example.org/research",
            },
            {
                "id": "APPROVAL-001",
                "evidence_type": "approval_record",
                "access_classification": "RESTRICTED",
                "publication_permission": False,
            },
        ],
        "claims": [
            {
                "claim_id": "CLAIM-001",
                "category": "CULTURAL_PRACTICE",
                "text": "Example claim supported by the referenced public source.",
                "status": "CORROBORATED",
                "public": True,
                "evidence_ids": ["SRC-001"],
            }
        ],
        "reviews": {
            "cultural": {
                "status": "PASS",
                "reviewer_ref": "COMMUNITY-REVIEWER-REF",
                "evidence_ids": ["APPROVAL-001"],
            },
            "independent_qa": {
                "status": "PASS",
                "reviewer_ref": "INDEPENDENT-QA-REF",
                "evidence_ids": ["APPROVAL-001"],
            },
            "community_publication": {
                "status": "PASS",
                "reviewer_ref": "COMMUNITY-AUTHORITY-REF",
                "evidence_ids": ["APPROVAL-001"],
                "artifact_sha256": artifact_sha,
            },
            "scientific": {
                "status": "NOT_STARTED",
                "reviewer_ref": None,
                "evidence_ids": [],
            },
        },
        "food_safety": {"status": "NOT_ASSESSED", "evidence_ids": []},
        "publication": {
            "status": "APPROVED",
            "artifact_sha256": artifact_sha,
            "channels": ["KMH Heritage Portal"],
            "languages": ["my", "en"],
            "approval_evidence_ids": ["APPROVAL-001"],
        },
    }


class LaphetPublicationGateTests(unittest.TestCase):
    def test_happy_path_requires_all_named_gates(self):
        result = assess_publication_readiness(ready_record())
        self.assertTrue(result["eligible"], result["errors"])

    def test_empty_or_gate_zero_record_is_held(self):
        result = assess_publication_readiness({
            "record_status": "HOLD",
            "access_classification": "RESTRICTED",
            "evidence": [],
            "claims": [],
        })
        self.assertFalse(result["eligible"])
        self.assertTrue(any("APPROVED_FOR_PUBLICATION" in error for error in result["errors"]))

    def test_withdrawn_consent_blocks_publication(self):
        record = ready_record()
        record["consent"]["status"] = "WITHDRAWN"
        result = assess_publication_readiness(record)
        self.assertFalse(result["eligible"])
        self.assertTrue(any("consent.status" in error for error in result["errors"]))

    def test_restricted_evidence_cannot_support_public_claim(self):
        record = ready_record()
        record["claims"][0]["evidence_ids"] = ["CONSENT-001"]
        result = assess_publication_readiness(record)
        self.assertFalse(result["eligible"])
        self.assertTrue(any("non-public evidence" in error for error in result["errors"]))

    def test_claim_without_permission_is_blocked(self):
        record = ready_record()
        record["evidence"][1]["publication_permission"] = False
        result = assess_publication_readiness(record)
        self.assertFalse(result["eligible"])
        self.assertTrue(any("without publication permission" in error for error in result["errors"]))

    def test_disputed_claim_is_not_publishable(self):
        record = ready_record()
        record["claims"][0]["status"] = "DISPUTED"
        result = assess_publication_readiness(record)
        self.assertFalse(result["eligible"])
        self.assertTrue(any("supported, corroborated" in error for error in result["errors"]))

    def test_named_attribution_needs_separate_permission(self):
        record = ready_record()
        record["attribution_mode"] = "NAMED"
        result = assess_publication_readiness(record)
        self.assertFalse(result["eligible"])
        self.assertTrue(any("attribution consent" in error for error in result["errors"]))

    def test_artifact_must_match_community_approval(self):
        record = ready_record()
        record["publication"]["artifact_sha256"] = "b" * 64
        result = assess_publication_readiness(record)
        self.assertFalse(result["eligible"])
        self.assertTrue(any("exact publication artifact hash" in error for error in result["errors"]))

    def test_health_claims_are_out_of_scope(self):
        record = ready_record()
        record["claims"][0]["category"] = "HEALTH"
        result = assess_publication_readiness(record)
        self.assertFalse(result["eligible"])
        self.assertTrue(any("health/medical claims" in error for error in result["errors"]))

    def test_food_safety_claim_requires_batch_specific_lab_report(self):
        record = ready_record()
        record["claims"][0]["category"] = "FOOD_SAFETY"
        record["food_safety"] = {"status": "NOT_ASSESSED", "evidence_ids": []}
        result = assess_publication_readiness(record)
        self.assertFalse(result["eligible"])
        self.assertTrue(any("laboratory report" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
