import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'production-runtime-artifact-attestation.yml'
PHASE_DOC = ROOT / 'docs' / 'phase_810_protected_release_workflow.md'
PHASE_809_DOC = ROOT / 'docs' / 'phase_809_release_context_binding.md'
PHASE_811_DOC = ROOT / 'docs' / 'phase_811_production_trust_artifact_readiness.md'
PHASE_812_DOC = ROOT / 'docs' / 'phase_812_immutable_build_artifact_provenance.md'

class ProtectedRuntimeArtifactAttestationWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow = WORKFLOW.read_text(encoding='utf-8')
        self.phase_doc = PHASE_DOC.read_text(encoding='utf-8')
        self.phase_809_doc = PHASE_809_DOC.read_text(encoding='utf-8')
        self.phase_811_doc = PHASE_811_DOC.read_text(encoding='utf-8')
        self.phase_812_doc = PHASE_812_DOC.read_text(encoding='utf-8')

    def test_manual_dispatch_only_and_explicit_producer_artifact_inputs(self):
        triggers = self.workflow.split('jobs:', 1)[0]
        self.assertIn('workflow_dispatch:', triggers)
        self.assertNotIn('  pull_request:', triggers)
        self.assertNotIn('  push:', triggers)
        for name in ('producer_run_id', 'producer_workflow_path', 'producer_source_sha', 'runtime_artifact_id', 'runtime_artifact_name', 'runtime_artifact_digest', 'expected_release_sha'):
            self.assertIn(f'{name}:', triggers)
        self.assertIn('producer SHA must exactly match expected release SHA', self.workflow)

    def test_signing_requires_manual_main_and_protected_environment(self):
        self.assertGreaterEqual(self.workflow.count("github.ref == 'refs/heads/main'"), 2)
        self.assertGreaterEqual(self.workflow.count("github.event_name == 'workflow_dispatch'"), 2)
        self.assertIn('name: production-attestation', self.workflow)
        self.assertIn('needs: [preflight]', self.workflow)
        self.assertIn("needs.preflight.result == 'success'", self.workflow)

    def test_producer_workflow_and_artifact_are_allowlisted_and_api_verified(self):
        self.assertIn('.github/workflows/trusted-runtime-build.yml', self.workflow)
        self.assertIn('actions/runs/{run_id}', self.workflow)
        self.assertIn('run.get(field) != value', self.workflow)
        self.assertIn('actions/runs/{run_id}/artifacts', self.workflow)
        self.assertIn("artifact.get('digest') != os.environ['RUNTIME_ARTIFACT_DIGEST']", self.workflow)
        self.assertIn("str(a.get('id')) == os.environ['RUNTIME_ARTIFACT_ID']", self.workflow)

    def test_signer_downloads_by_artifact_id_and_checks_real_bytes_digest(self):
        self.assertIn('actions/artifacts/$RUNTIME_ARTIFACT_ID/zip', self.workflow)
        self.assertIn('sha256sum runtime-artifact.zip', self.workflow)
        self.assertIn('test "$actual" = "$EXPECTED_ARTIFACT_DIGEST"', self.workflow)
        self.assertIn('verified-runtime-artifact/classifier.bin', self.workflow)
        self.assertIn('verified-runtime-artifact/policy.bin', self.workflow)
        self.assertNotIn('inputs.classifier_artifact_path', self.workflow)
        self.assertNotIn('inputs.policy_artifact_path', self.workflow)

    def test_private_key_is_step_scoped_and_never_echoed(self):
        begin = self.workflow.index('- name: Create signed attestation')
        end = self.workflow.index('- name: Upload run-scoped attestation evidence')
        signing_step = self.workflow[begin:end]
        self.assertIn('secrets.KMH_OIA_ATTESTATION_PRIVATE_KEY_B64', signing_step)
        self.assertNotIn('echo $KMH_OIA_ATTESTATION_PRIVATE_KEY_B64', self.workflow)
        self.assertNotIn('printenv', self.workflow)
        self.assertNotIn('set -x', self.workflow)

    def test_attestation_tracks_producer_run_not_signing_run(self):
        self.assertIn('GITHUB_RUN_ID: ${{ inputs.producer_run_id }}', self.workflow)
        self.assertIn('--build-run-id "$GITHUB_RUN_ID"', self.workflow)
        self.assertNotIn('GITHUB_RUN_ID: ${{ github.run_id }}', self.workflow)
        self.assertIn('runtime-artifact-attestation-${{ inputs.producer_run_id }}', self.workflow)

    def test_external_environment_controls_remain_unverified_and_release_is_hold(self):
        self.assertIn('not verified by this commit', self.phase_doc.lower())
        self.assertIn('required reviewers', self.phase_doc.lower())
        self.assertIn('Production HOLD', self.phase_doc)
        self.assertIn('Production HOLD', self.phase_811_doc)
        self.assertIn('Production HOLD', self.phase_812_doc)

    def test_phase_809_and_812_limits_are_recorded(self):
        self.assertIn('before production run-context checks', self.phase_809_doc)
        self.assertIn('the producer workflow is not yet implemented', self.phase_812_doc.lower())

if __name__ == '__main__':
    unittest.main()
