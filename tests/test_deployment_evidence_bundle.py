import unittest

from scripts.deployment_evidence_bundle import (
    EXPECTED_SMOKE_TEST,
    build_bundle,
)


def passing_target(commit_sha="abc123", database_path="/var/lib/kmh-oia/replay.sqlite3"):
    return {
        "environment_id": "staging-1",
        "host_or_service_id": "service-1",
        "persistent_volume_confirmed": True,
        "database_path": database_path,
        "smoke_test_report": {
            "schema_version": "1.0",
            "test": EXPECTED_SMOKE_TEST,
            "db_path": database_path,
            "first_process": {
                "healthy": True,
                "accepted": True,
                "reason": "accepted",
            },
            "second_process": {
                "healthy": True,
                "accepted": False,
                "reason": "replay_detected",
            },
            "result": "PASS",
        },
        "smoke_tested_at_utc": "2026-10-20T09:00:00Z",
        "commit_sha": commit_sha,
    }


def target_gate(result):
    return next(
        gate for gate in result["gates"]
        if gate["gate"] == "target_host_persistent_storage_and_process_replay"
    )


class DeploymentEvidenceBundleTests(unittest.TestCase):
    def test_missing_target_evidence_never_passes_deployment(self):
        result = build_bundle(
            commit_sha="abc123",
            ci_runs=[{
                "name": "Tests",
                "url": "https://example.invalid/run",
                "head_sha": "abc123",
                "conclusion": "success",
            }],
        )
        gates = {gate["gate"]: gate for gate in result["gates"]}
        self.assertEqual(gates["repository_ci_for_bundle_commit"]["status"], "PASS")
        self.assertEqual(gates["target_host_persistent_storage_and_process_replay"]["status"], "NOT_VERIFIED")
        self.assertEqual(gates["external_business_outcome"]["status"], "HOLD")
        self.assertEqual(result["release_decision"], "HOLD")

    def test_complete_smoke_receipt_volume_confirmation_and_same_sha_pass_target_gate(self):
        result = build_bundle(
            commit_sha="abc123",
            ci_runs=[{"name": "Tests", "head_sha": "abc123", "conclusion": "success"}],
            target_evidence=passing_target(),
        )
        gates = {gate["gate"]: gate for gate in result["gates"]}
        self.assertEqual(gates["target_host_persistent_storage_and_process_replay"]["status"], "PASS")
        self.assertEqual(gates["real_provider_authenticity_and_execution_attribution"]["status"], "NOT_VERIFIED")
        self.assertEqual(gates["external_business_outcome"]["status"], "HOLD")
        self.assertEqual(result["release_decision"], "HOLD")

    def test_minimal_fake_pass_receipt_is_rejected(self):
        target = passing_target()
        target["smoke_test_report"] = {"result": "PASS"}
        gate = target_gate(build_bundle(
            commit_sha="abc123",
            ci_runs=[{"name": "Tests", "head_sha": "abc123", "conclusion": "success"}],
            target_evidence=target,
        ))
        self.assertEqual(gate["status"], "NOT_VERIFIED")
        self.assertTrue(any("missing schema_version" in error for error in gate["validation_errors"]))

    def test_smoke_report_database_path_must_match_declared_database(self):
        target = passing_target()
        target["smoke_test_report"]["db_path"] = "/tmp/other.sqlite3"
        gate = target_gate(build_bundle(
            commit_sha="abc123",
            ci_runs=[{"name": "Tests", "head_sha": "abc123", "conclusion": "success"}],
            target_evidence=target,
        ))
        self.assertEqual(gate["status"], "NOT_VERIFIED")
        self.assertIn("smoke_test_report db_path must match database_path", gate["validation_errors"])

    def test_smoke_report_requires_first_claim_accepted_and_duplicate_rejected(self):
        target = passing_target()
        target["smoke_test_report"]["second_process"]["accepted"] = True
        gate = target_gate(build_bundle(
            commit_sha="abc123",
            ci_runs=[{"name": "Tests", "head_sha": "abc123", "conclusion": "success"}],
            target_evidence=target,
        ))
        self.assertEqual(gate["status"], "NOT_VERIFIED")

    def test_target_evidence_for_a_different_commit_does_not_pass(self):
        gate = target_gate(build_bundle(
            commit_sha="new-sha",
            ci_runs=[{"name": "Tests", "head_sha": "new-sha", "conclusion": "success"}],
            target_evidence=passing_target(commit_sha="old-sha"),
        ))
        self.assertEqual(gate["status"], "NOT_VERIFIED")

    def test_timezone_must_be_valid_and_utc(self):
        for value in ("2026-10-20T09:00:00", "not-a-date", "2026-10-20T12:00:00+03:00"):
            with self.subTest(value=value):
                target = passing_target()
                target["smoke_tested_at_utc"] = value
                gate = target_gate(build_bundle(
                    commit_sha="abc123",
                    ci_runs=[{"name": "Tests", "head_sha": "abc123", "conclusion": "success"}],
                    target_evidence=target,
                ))
                self.assertEqual(gate["status"], "NOT_VERIFIED")

    def test_volume_confirmation_must_be_boolean_true(self):
        target = passing_target()
        target["persistent_volume_confirmed"] = "true"
        gate = target_gate(build_bundle(
            commit_sha="abc123",
            ci_runs=[{"name": "Tests", "head_sha": "abc123", "conclusion": "success"}],
            target_evidence=target,
        ))
        self.assertEqual(gate["status"], "NOT_VERIFIED")

    def test_ci_runs_for_another_commit_do_not_pass_ci_gate(self):
        result = build_bundle(
            commit_sha="new-sha",
            ci_runs=[{"name": "Tests", "head_sha": "old-sha", "conclusion": "success"}],
        )
        ci = next(gate for gate in result["gates"] if gate["gate"] == "repository_ci_for_bundle_commit")
        self.assertEqual(ci["status"], "NOT_VERIFIED")

    def test_optional_non_required_run_does_not_block_required_green_run(self):
        result = build_bundle(
            commit_sha="sha-1",
            ci_runs=[
                {"name": "Tests", "head_sha": "sha-1", "conclusion": "success"},
                {
                    "name": "Informational check",
                    "head_sha": "sha-old",
                    "conclusion": "failure",
                    "is_required_check": False,
                },
            ],
        )
        ci = next(gate for gate in result["gates"] if gate["gate"] == "repository_ci_for_bundle_commit")
        self.assertEqual(ci["status"], "PASS")
        self.assertFalse(ci["evidence"][1]["matches_bundle_commit"])
        self.assertFalse(ci["evidence"][1]["is_required_check"])

    def test_failed_required_run_blocks_ci_gate_even_when_another_passes(self):
        result = build_bundle(
            commit_sha="sha-1",
            ci_runs=[
                {"name": "Tests", "head_sha": "sha-1", "conclusion": "success"},
                {"name": "Validation", "head_sha": "sha-1", "conclusion": "failure"},
            ],
        )
        ci = next(gate for gate in result["gates"] if gate["gate"] == "repository_ci_for_bundle_commit")
        self.assertEqual(ci["status"], "NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
