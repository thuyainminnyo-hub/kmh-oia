import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'production-runtime-artifact-attestation.yml'
DOC = ROOT / 'docs' / 'phase_813_trusted_runtime_artifact_handoff.md'

class TrustedRuntimeArtifactHandoffContractTests(unittest.TestCase):
    def test_signer_uses_producer_id_and_not_current_signing_run(self):
        workflow = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('GITHUB_RUN_ID: ${{ inputs.producer_run_id }}', workflow)
        self.assertNotIn('GITHUB_RUN_ID: ${{ github.run_id }}', workflow)
        self.assertIn('--build-run-id "$GITHUB_RUN_ID"', workflow)

    def test_no_source_tree_fallback_and_immutable_download_are_required(self):
        workflow = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('.github/workflows/trusted-runtime-build.yml', workflow)
        self.assertNotIn('inputs.classifier_artifact_path', workflow)
        self.assertNotIn('inputs.policy_artifact_path', workflow)
        self.assertIn('Download the artifact by immutable ID', workflow)
        self.assertIn('sha256sum runtime-artifact.zip', workflow)

    def test_phase_document_records_external_prerequisites(self):
        content = DOC.read_text(encoding='utf-8')
        self.assertIn('fail-closed', content.lower())
        self.assertIn('has not been implemented', content.lower())
        self.assertIn('Production remains HOLD', content)

if __name__ == '__main__':
    unittest.main()
