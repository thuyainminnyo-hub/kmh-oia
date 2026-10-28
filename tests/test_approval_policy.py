"""Tests for approval identity/policy separation from signing authority."""
import unittest

from src.approval_policy import (
    ApprovalCheck,
    ApprovalRecord,
    validate_independent_approval,
)


class FakeApprovalAuthority:
    def __init__(self, record=None, authorized=True, fail=False):
        self.record = record
        self.authorized = authorized
        self.fail = fail

    def resolve_approval(self, approval_id):
        if self.fail:
            raise RuntimeError("authority unavailable")
        return self.record

    def is_authorized_approver(self, approver_id, policy_id):
        if self.fail:
            raise RuntimeError("authorization unavailable")
        return self.authorized


def record(**overrides):
    values = dict(
        approval_id="approval:001",
        approver_id="human-reviewer:007",
        evidence_id="evidence:001",
        qa_id="qa:001",
        source_revision="a" * 40,
        decision="APPROVE",
        policy_id="release-policy:v1",
        approved_at="2026-10-21T01:00:00Z",
    )
    values.update(overrides)
    return ApprovalRecord(**values)


class ApprovalPolicyTests(unittest.TestCase):
    def validate(self, authority, **kwargs):
        values = dict(
            approval_id="approval:001",
            evidence_id="evidence:001",
            qa_id="qa:001",
            source_revision="a" * 40,
            signing_service_id="service:release-signer",
            accepted_policy_ids={"release-policy:v1"},
        )
        values.update(kwargs)
        return validate_independent_approval(authority, **values)

    def test_matching_independent_approval_passes(self):
        result = self.validate(FakeApprovalAuthority(record()))
        self.assertTrue(result.passed)
        self.assertEqual(result.approver_id, "human-reviewer:007")

    def test_missing_or_untrusted_record_fails_closed(self):
        self.assertFalse(self.validate(FakeApprovalAuthority(None)).passed)
        self.assertFalse(self.validate(FakeApprovalAuthority(record()), approval_id=None).passed)

    def test_approver_must_be_independent_of_signing_service(self):
        result = self.validate(FakeApprovalAuthority(record(approver_id="service:release-signer")))
        self.assertFalse(result.passed)
        self.assertIn("independent", result.reason)

    def test_evidence_qa_and_revision_scope_must_match(self):
        for kwargs in (
            {"evidence_id": "evidence:other"},
            {"qa_id": "qa:other"},
            {"source_revision": "b" * 40},
            {"source_revision": "unresolved"},
        ):
            with self.subTest(kwargs=kwargs):
                self.assertFalse(self.validate(FakeApprovalAuthority(record()), **kwargs).passed)

    def test_policy_and_identity_authorization_are_required(self):
        self.assertFalse(
            self.validate(FakeApprovalAuthority(record()), accepted_policy_ids={"other"}).passed
        )
        self.assertFalse(self.validate(FakeApprovalAuthority(record(), authorized=False)).passed)

    def test_approval_service_errors_fail_closed(self):
        result = self.validate(FakeApprovalAuthority(record(), fail=True))
        self.assertFalse(result.passed)
        self.assertIn("unavailable", result.reason)

    def test_non_approve_decision_is_rejected(self):
        result = self.validate(FakeApprovalAuthority(record(decision="REJECT")))
        self.assertFalse(result.passed)

    def test_approval_reference_must_match_record(self):
        result = self.validate(FakeApprovalAuthority(record(approval_id="approval:other")))
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
