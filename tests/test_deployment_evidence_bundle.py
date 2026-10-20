import unittest

from scripts.deployment_evidence_bundle import EXPECTED_SMOKE_TEST, build_bundle


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
            "first_process": {"healthy": True, "accepted": True, "reason": "accepted"},
            "second_process": {"healthy": True, "accepted": False, "reason": "replay_detected"},
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
            ci_runs=[{"name": "Tests", "url": "https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/1", "head_sha": "abc123", "conclusion": "success", "is_required_check": True}],
        )
        gates = {gate["gate"]: gate for gate in result["gates"]}
        self.assertEqual(gates["repository_ci_for_bundle_commit"]["status"], "PASS")
        self.assertEqual(gates["target_host_persistent_storage_and_process_replay"]["status"], "NOT_VERIFIED")
        self.assertEqual(gates["external_business_outcome"]["status"], "HOLD")
        self.assertEqual(result["release_decision"], "HOLD")

    def test_complete_smoke_receipt_volume_confirmation_and_same_sha_pass_target_gate(self):
        result = build_bundle(
            commit_sha="abc123",
            ci_runs=[{"name": "Tests", "url": "https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/1", "head_sha": "abc123", "conclusion": "success", "is_required_check": True}],
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
        gate = target_gate(build_bundle(commit_sha="abc123", ci_runs=[], target_evidence=target))
        self.assertEqual(gate["status"], "NOT_VERIFIED")
        self.assertTrue(any("missing schema_version" in e for e in gate["validation_errors"]))

    def test_smoke_report_database_path_must_match_declared_database(self):
        target = passing_target()
        target["smoke_test_report"]["db_path"] = "/tmp/other.sqlite3"
        gate = target_gate(build_bundle(commit_sha="abc123", ci_runs=[], target_evidence=target))
        self.assertEqual(gate["status"], "NOT_VERIFIED")
        self.assertIn("smoke_test_report db_path must match database_path", gate["validation_errors"])

    def test_smoke_report_requires_first_claim_accepted_and_duplicate_rejected(self):
        target = passing_target()
        target["smoke_test_report"]["second_process"]["accepted"] = True
        gate = target_gate(build_bundle(commit_sha="abc123", ci_runs=[], target_evidence=target))
        self.assertEqual(gate["status"], "NOT_VERIFIED")

    def test_target_evidence_for_a_different_commit_does_not_pass(self):
        gate = target_gate(build_bundle(commit_sha="new-sha", ci_runs=[], target_evidence=passing_target(commit_sha="old-sha")))
        self.assertEqual(gate["status"], "NOT_VERIFIED")

    def test_timezone_must_be_valid_and_utc(self):
        for value in ("2026-10-20T09:00:00", "not-a-date", "2026-10-20T12:00:00+03:00"):
            with self.subTest(value=value):
                target = passing_target()
                target["smoke_tested_at_utc"] = value
                gate = target_gate(build_bundle(commit_sha="abc123", ci_runs=[], target_evidence=target))
                self.assertEqual(gate["status"], "NOT_VERIFIED")

    def test_volume_confirmation_must_be_boolean_true(self):
        target = passing_target()
        target["persistent_volume_confirmed"] = "true"
        gate = target_gate(build_bundle(commit_sha="abc123", ci_runs=[], target_evidence=target))
        self.assertEqual(gate["status"], "NOT_VERIFIED")

    def test_ci_runs_for_another_commit_do_not_pass_ci_gate(self):
        result = build_bundle(commit_sha="new-sha", ci_runs=[{"name": "Tests", "url": "https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/1", "head_sha": "old-sha", "conclusion": "success", "is_required_check": True}])
        ci = next(g for g in result["gates"] if g["gate"] == "repository_ci_for_bundle_commit")
        self.assertEqual(ci["status"], "NOT_VERIFIED")

    def test_optional_non_required_run_does_not_block_required_green_run(self):
        result = build_bundle(commit_sha="sha-1", ci_runs=[
            {"name": "Tests", "url": "https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/1", "head_sha": "sha-1", "conclusion": "success", "is_required_check": True},
            {"name": "Informational check", "url": "https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/2", "head_sha": "sha-old", "conclusion": "failure", "is_required_check": False},
        ])
        ci = next(g for g in result["gates"] if g["gate"] == "repository_ci_for_bundle_commit")
        self.assertEqual(ci["status"], "PASS")
        self.assertFalse(ci["evidence"][1]["matches_bundle_commit"])
        self.assertFalse(ci["evidence"][1]["is_required_check"])

    def test_failed_required_run_blocks_ci_gate_even_when_another_passes(self):
        result = build_bundle(commit_sha="sha-1", ci_runs=[
            {"name": "Tests", "url": "https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/1", "head_sha": "sha-1", "conclusion": "success", "is_required_check": True},
            {"name": "Validation", "url": "https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/2", "head_sha": "sha-1", "conclusion": "failure", "is_required_check": True},
        ])
        ci = next(g for g in result["gates"] if g["gate"] == "repository_ci_for_bundle_commit")
        self.assertEqual(ci["status"], "NOT_VERIFIED")

    def test_required_ci_row_needs_complete_metadata_and_github_run_url(self):
        result = build_bundle(
            commit_sha="sha-1",
            ci_runs=[{
                "name": "Tests",
                "url": "not-a-url",
                "head_sha": "sha-1",
                "conclusion": "success",
                "is_required_check": True,
            }],
        )
        ci = next(g for g in result["gates"] if g["gate"] == "repository_ci_for_bundle_commit")
        self.assertEqual(ci["status"], "NOT_VERIFIED")
        self.assertTrue(any("GitHub HTTPS run URL" in error for error in ci["validation_errors"]))

    def test_missing_required_ci_check_flag_does_not_default_to_required_pass(self):
        result = build_bundle(
            commit_sha="sha-1",
            ci_runs=[{
                "name": "Tests",
                "url": "https://github.com/example/repo/actions/runs/1",
                "head_sha": "sha-1",
                "conclusion": "success",
            }],
        )
        ci = next(g for g in result["gates"] if g["gate"] == "repository_ci_for_bundle_commit")
        self.assertEqual(ci["status"], "NOT_VERIFIED")
        self.assertIn("missing is_required_check", ci["validation_errors"][0])

    def test_malformed_optional_check_is_visible_but_does_not_block_valid_required_check(self):
        result = build_bundle(
            commit_sha="sha-1",
            ci_runs=[
                {
                    "name": "Tests",
                    "url": "https://github.com/example/repo/actions/runs/1",
                    "head_sha": "sha-1",
                    "conclusion": "success",
                    "is_required_check": True,
                },
                {
                    "name": "",
                    "url": "invalid",
                    "head_sha": "old-sha",
                    "conclusion": "failure",
                    "is_required_check": False,
                },
            ],
        )
        ci = next(g for g in result["gates"] if g["gate"] == "repository_ci_for_bundle_commit")
        self.assertEqual(ci["status"], "PASS")
        self.assertTrue(ci["evidence"][1]["validation_errors"])


def test_release_decision_never_promotes_with_missing_target_evidence(self):
    result = build_bundle(
        commit_sha="abc123",
        ci_runs=[{
            "name": "Tests",
            "url": "https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/1",
            "head_sha": "abc123",
            "conclusion": "success",
            "is_required_check": True,
        }],
    )
    self.assertEqual(result["release_decision"], "HOLD")
    target = target_gate(result)
    self.assertEqual(target["status"], "NOT_VERIFIED")

def test_target_evidence_with_wrong_sha_cannot_pass_even_with_green_ci(self):
    result = build_bundle(
        commit_sha="new-sha",
        ci_runs=[{
            "name": "Tests",
            "url": "https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/1",
            "head_sha": "new-sha",
            "conclusion": "success",
            "is_required_check": True,
        }],
        target_evidence=passing_target(commit_sha="old-sha"),
    )
    self.assertEqual(next(g for g in result["gates"] if g["gate"] == "repository_ci_for_bundle_commit")["status"], "PASS")
    self.assertEqual(target_gate(result)["status"], "NOT_VERIFIED")
    self.assertEqual(result["release_decision"], "HOLD")

    def test_verified_target_host_does_not_clear_unverified_provider_or_outcome(self):
        result = build_bundle(
            commit_sha="abc123",
            ci_runs=[{
                "name": "Tests",
                "url": "https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/1",
                "head_sha": "abc123",
                "conclusion": "success",
                "is_required_check": True,
            }],
            target_evidence=passing_target(commit_sha="abc123"),
        )
        gates = {gate["gate"]: gate for gate in result["gates"]}
        self.assertEqual(gates["repository_ci_for_bundle_commit"]["status"], "PASS")
        self.assertEqual(gates["target_host_persistent_storage_and_process_replay"]["status"], "PASS")
        self.assertEqual(gates["real_provider_authenticity_and_execution_attribution"]["status"], "NOT_VERIFIED")
        self.assertEqual(gates["external_business_outcome"]["status"], "HOLD")
        self.assertEqual(gates["multi_host_replay"]["status"], "NOT_VERIFIED")
        self.assertEqual(result["release_decision"], "HOLD")

    def test_no_ci_rows_cannot_make_repository_ci_gate_pass(self):
        result = build_bundle(commit_sha="abc123", ci_runs=[])
        ci = next(g for g in result["gates"] if g["gate"] == "repository_ci_for_bundle_commit")
        self.assertEqual(ci["status"], "NOT_VERIFIED")
        self.assertEqual(result["release_decision"], "HOLD")


if __name__ == "__main__":
    unittest.main()
