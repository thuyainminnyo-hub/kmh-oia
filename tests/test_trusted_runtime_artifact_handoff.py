import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github' / 'workflows' / 'production-runtime-artifact-attestation.yml'
PRODUCER = ROOT / '.github' / 'workflows' / 'trusted-build.yml'
DOC = ROOT / 'docs' / 'phase_813_trusted_runtime_artifact_handoff.md'

class TrustedRuntimeArtifactHandoffContractTests(unittest.TestCase):
    def test_signer_uses_producer_id_and_not_current_signing_run(self):
        workflow = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('GITHUB_RUN_ID: ${{ inputs.producer_run_id }}', workflow)
        self.assertNotIn('GITHUB_RUN_ID: ${{ github.run_id }}', workflow)
        self.assertIn('--build-run-id "$GITHUB_RUN_ID"', workflow)

    def test_bundle_contract_is_produced_and_verified(self):
        workflow = WORKFLOW.read_text(encoding='utf-8')
        producer = PRODUCER.read_text(encoding='utf-8')
        self.assertIn('.github/workflows/trusted-build.yml', workflow)
        self.assertIn('kmh-oia-runtime-bundle', workflow)
        self.assertIn('kmh-oia-runtime-bundle', producer)
        self.assertIn('runtime-source-bundle.tar.gz', producer)
        self.assertIn('runtime-source-bundle.tar.gz', workflow)
        self.assertIn('scripts/validate_runtime_bundle.py', workflow)
        self.assertNotIn('classifier.bin', workflow)
        self.assertNotIn('policy.bin', workflow)

    def test_source_bundle_is_deterministic_and_manifest_bound(self):
        package_script = (ROOT / 'scripts' / 'package_runtime_bundle.py').read_text(encoding='utf-8')
        validator = (ROOT / 'scripts' / 'validate_runtime_bundle.py').read_text(encoding='utf-8')
        self.assertIn('mtime=0', package_script)
        self.assertIn('MANIFEST.json', package_script)
        self.assertIn('MANIFEST.json', validator)
        self.assertIn('manifest SHA-256 mismatch', validator)

    def test_external_controls_and_production_hold_remain_explicit(self):
        content = DOC.read_text(encoding='utf-8')
        self.assertIn('fail-closed', content.lower())
        self.assertIn('Production HOLD', content)
        self.assertIn('not proof of deployment', content.lower())

if __name__ == '__main__':
    unittest.main()
