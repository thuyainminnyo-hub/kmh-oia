"""Unit tests for the side-effect-free cybersecurity executor contract."""
import unittest
from datetime import datetime, timezone

from src.cybersecurity_executor_contract import (
    RemediationRequest,
    RemediationResult,
    RemediationStatus,
)

UTC = timezone.utc
START = datetime(2026, 10, 27, 10, 0, tzinfo=UTC)
END = datetime(2026, 10, 27, 10, 1, tzinfo=UTC)


class RemediationRequestContractTests(unittest.TestCase):
    def valid_request(self, **overrides):
        values = {
            "command_id": "cmd-123",
            "case_id": "KMH-OIA-CYBER-2026-001",
            "registry_version": 1,
            "asset_id": "asset-staging-01",
            "action": "remediate",
            "approval_id": "approval-123",
            "idempotency_key": "cmd-123:case-001:v1:remediate",
            "requested_at": START,
        }
        values.update(overrides)
        return RemediationRequest(**values)

    def test_accepts_valid_immutable_request(self):
        request = self.valid_request()
        self.assertEqual(request.asset_id, "asset-staging-01")
        with self.assertRaises((AttributeError, TypeError)):
            request.asset_id = "another-asset"

    def test_rejects_missing_asset(self):
        with self.assertRaisesRegex(ValueError, "asset_id"):
            self.valid_request(asset_id=" ")

    def test_rejects_non_positive_or_boolean_version(self):
        for version in (0, -1, True):
            with self.subTest(version=version):
                with self.assertRaisesRegex(ValueError, "registry_version"):
                    self.valid_request(registry_version=version)

    def test_rejects_unsupported_action(self):
        with self.assertRaisesRegex(ValueError, "allowed cybersecurity action"):
            self.valid_request(action="delete")

    def test_rejects_naive_timestamp(self):
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            self.valid_request(requested_at=datetime(2026, 10, 27, 10, 0))


class RemediationResultContractTests(unittest.TestCase):
    def valid_result(self, **overrides):
        values = {
            "execution_id": "exec-123",
            "command_id": "cmd-123",
            "case_id": "KMH-OIA-CYBER-2026-001",
            "registry_version": 1,
            "asset_id": "asset-staging-01",
            "action": "remediate",
            "executor_id": "staging-remediator-v1",
            "target_id": "asset-staging-01",
            "started_at": START,
            "finished_at": END,
            "status": RemediationStatus.SUCCEEDED,
            "before_evidence_refs": ("evidence:before-001",),
            "action_evidence_refs": ("evidence:action-001",),
            "after_evidence_refs": ("evidence:after-001",),
        }
        values.update(overrides)
        return RemediationResult(**values)

    def test_accepts_structured_success_observation(self):
        result = self.valid_result()
        self.assertEqual(result.status, RemediationStatus.SUCCEEDED)
        self.assertEqual(result.before_evidence_refs, ("evidence:before-001",))

    def test_rejects_finished_time_before_start(self):
        with self.assertRaisesRegex(ValueError, "must not precede"):
            self.valid_result(finished_at=datetime(2026, 10, 27, 9, 59, tzinfo=UTC))

    def test_rejects_malformed_evidence_references(self):
        with self.assertRaisesRegex(ValueError, "tuple of non-empty strings"):
            self.valid_result(after_evidence_refs=("",))

    def test_failure_requires_structured_error_code(self):
        with self.assertRaisesRegex(ValueError, "error_code"):
            self.valid_result(status=RemediationStatus.FAILED, error_code=None)

    def test_non_success_status_requires_error_code(self):
        for status in (RemediationStatus.PARTIAL, RemediationStatus.UNKNOWN):
            with self.subTest(status=status):
                with self.assertRaisesRegex(ValueError, "error_code"):
                    self.valid_result(status=status, error_code=" ")

    def test_rejects_plain_string_status(self):
        with self.assertRaisesRegex(ValueError, "RemediationStatus"):
            self.valid_result(status="SUCCEEDED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
