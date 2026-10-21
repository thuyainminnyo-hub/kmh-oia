import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "production-runtime-artifact-attestation.yml"
PHASE_DOC = ROOT / "docs" / "phase_810_protected_release_workflow.md"
PHASE_809_DOC = ROOT / "docs" / "phase_809_release_context_binding.md"
PHASE_811_DOC = ROOT / "docs" / "phase_811_production_trust_artifact_readiness.md"


class ProtectedRuntimeArtifactAttestationWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow = WORKFLOW.read_text(encoding="utf-8")
        self.phase_doc = PHASE_DOC.read_text(encoding="utf-8")
        self.phase_809_doc = PHASE_809_DOC.read_text(encoding="utf-8")
        self.phase_811_doc = PHASE_811_DOC.read_text(encoding="utf-8")

    def test_manual_dispatch_only_and_explicit_artifact_inputs(self):
        triggers = self.workflow.split("jobs:", 1)[0]
        self.assertIn("workflow_dispatch:", triggers)
        self.assertNotIn("  pull_request:", triggers)
        self.assertNotIn("  push:", triggers)
        self.assertIn("classifier_artifact_path:", triggers)
        self.assertIn("policy_artifact_path:", triggers)

    def test_main_only_and_protected_environment(self):
        self.assertIn("github.ref == 'refs/heads/main'", self.workflow)
        self.assertIn("github.event_name == 'workflow_dispatch'", self.workflow)
        self.assertIn("name: production-attestation", self.workflow)
        self.assertIn("needs: [preflight]", self.workflow)
        self.assertIn("needs.preflight.result == 'success'", self.workflow)

    def test_private_key_is_step_scoped_and_never_echoed(self):
        begin = self.workflow.index("- name: Create signed attestation")
        end = self.workflow.index("- name: Upload run-scoped attestation evidence")
        signing_step = self.workflow[begin:end]
        self.assertIn("secrets.KMH_OIA_ATTESTATION_PRIVATE_KEY_B64", signing_step)
        self.assertNotIn("echo $KMH_OIA_ATTESTATION_PRIVATE_KEY_B64", self.workflow)
        self.assertNotIn("printenv", self.workflow)
        self.assertNotIn("set -x", self.workflow)

    def test_paths_are_confined_to_checkout_and_nonempty(self):
        self.assertGreaterEqual(self.workflow.count("resolved.is_relative_to(root)"), 2)
        self.assertGreaterEqual(self.workflow.count("resolved.stat().st_size == 0"), 2)
        self.assertIn("reject symlink escapes", self.workflow)

    def test_output_is_run_scoped_and_upload_fails_if_missing(self):
        self.assertIn('output="runtime-artifact-attestation-${GITHUB_RUN_ID}.json"', self.workflow)
        self.assertIn("if-no-files-found: error", self.workflow)
        self.assertIn("retention-days: 90", self.workflow)

    def test_input_contract_does_not_claim_provenance(self):
        self.assertIn("checked out at main", self.workflow)
        self.assertIn("does not prove build provenance", self.workflow)
        self.assertIn("does not establish build provenance", self.phase_811_doc.lower())
        self.assertIn("not a deployment receipt", self.phase_doc)

    def test_external_environment_controls_remain_unverified_and_release_is_hold(self):
        self.assertIn("not verified by this commit", self.phase_doc.lower())
        self.assertIn("required reviewers", self.phase_doc.lower())
        self.assertIn("Production HOLD", self.phase_doc)
        self.assertIn("Production HOLD", self.phase_811_doc)

    def test_phase_809_measurement_order_is_recorded(self):
        self.assertIn("before production run-context checks", self.phase_809_doc)


if __name__ == "__main__":
    unittest.main()
