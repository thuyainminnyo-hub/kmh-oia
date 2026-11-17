import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from src.execution_identity import ExecutionIdentity, ExecutionIdentityContext
from src.production_evidence import ProductionEvidence
from src.verified_snapshot_store import VerifiedArtifactStore

class ProductionEvidenceTests(unittest.TestCase):
    def build(self, root, payload=b"synthetic image fixture"):
        outputs=root/"outputs"; outputs.mkdir(exist_ok=True)
        source=outputs/"artifact.bin"; source.write_bytes(payload)
        store=VerifiedArtifactStore(root/"store")
        snapshot=store.put_verified(source,allowed_root=outputs,artifact_id="job-job-1")
        return ProductionEvidence.from_snapshot(job_id="job-1",adapter_name="fake",output_path=str(source),
            snapshot=snapshot,elapsed_ms=125,provider_execution_id="provider-123",
            context=ExecutionIdentityContext(ExecutionIdentity("a","i","prod","s"),"cmd-1","exec-1"))
    def test_builds_manifest_from_verified_snapshot_and_pending_qa(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); evidence=self.build(root)
            self.assertEqual(evidence.output_sha256,hashlib.sha256(b"synthetic image fixture").hexdigest())
            self.assertEqual(evidence.output_size_bytes,len(b"synthetic image fixture"))
            self.assertEqual(evidence.qa_decision,"pending"); self.assertEqual(evidence.provider_execution_id,"provider-123")
            self.assertTrue(evidence.snapshot_reference.startswith("sha256/"))
    def test_json_is_stable_and_preserves_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence=self.build(Path(tmp)); parsed=json.loads(evidence.to_json())
            self.assertEqual(parsed["qa_decision"],"pending"); self.assertEqual(parsed["execution_id"],"exec-1")
            self.assertEqual(parsed["identity_key"],ExecutionIdentity("a","i","prod","s").key)
    def test_invalid_digest_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            ProductionEvidence(job_id="job",adapter_name="fake",output_path="/tmp/out",output_sha256="bad",
                output_size_bytes=1,elapsed_ms=0,provider_execution_id=None,snapshot_reference="ref",
                artifact_id="asset",execution_id="exec",command_id="cmd",identity_key="key",verification_version="v1")
if __name__=="__main__": unittest.main()
