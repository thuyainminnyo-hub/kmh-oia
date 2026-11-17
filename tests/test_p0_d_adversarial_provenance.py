import hashlib,tempfile,unittest
from pathlib import Path
from src.execution_identity import ExecutionIdentity,ExecutionIdentityContext
from src.production_evidence_gate import create_verified_evidence
from src.verified_snapshot_store import VerifiedArtifactStore
class P0DAdversarialTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.root=Path(self.temp.name)
  self.allowed=self.root/"allowed"; self.allowed.mkdir(); self.store=VerifiedArtifactStore(self.root/"store")
  self.source=self.allowed/"asset.bin"; self.source.write_bytes(b"source bytes")
 def context(self,job): return ExecutionIdentityContext(ExecutionIdentity("acct","inst","prod","sess"),"cmd-"+job,"exec-"+job,job)
 def evidence(self,job="job-1",source=None):
  return create_verified_evidence(job_id=job,adapter_name="fake",output_path=str(source or self.source),allowed_output_root=self.allowed,
   elapsed_ms=1,provider_execution_id="provider",execution_context=self.context(job),snapshot_store=self.store)
 def test_evidence_digest_matches_persisted_snapshot(self):
  evidence=self.evidence(); ref=self.store.recover()[0]
  self.assertEqual(evidence.output_sha256,hashlib.sha256(self.store.get_verified(ref)).hexdigest())
 def test_snapshot_artifact_id_is_bound_to_job(self):
  first=self.evidence("job-one"); second_source=self.allowed/"second.bin"; second_source.write_bytes(b"second bytes")
  second=self.evidence("job-two",second_source)
  self.assertEqual(first.artifact_id,"job-job-one"); self.assertEqual(second.artifact_id,"job-job-two")
  self.assertNotEqual(first.artifact_id,second.artifact_id)
 def test_rejects_duplicate_job_artifact_id(self):
  self.evidence("same-job")
  with self.assertRaises(FileExistsError): self.evidence("same-job")
 def test_execution_and_command_identity_are_recorded(self):
  evidence=self.evidence(); self.assertEqual((evidence.execution_id,evidence.command_id),("exec-job-1","cmd-job-1"))
 def test_missing_identity_context_is_rejected(self):
  with self.assertRaises(ValueError):
   create_verified_evidence(job_id="job",adapter_name="fake",output_path=str(self.source),allowed_output_root=self.allowed,
    elapsed_ms=1,provider_execution_id=None,execution_context=None,snapshot_store=self.store)
 def test_rejects_context_from_another_job(self):
  with self.assertRaisesRegex(ValueError,"context job_id"):
   create_verified_evidence(job_id="job-a",adapter_name="fake",output_path=str(self.source),allowed_output_root=self.allowed,
    elapsed_ms=1,provider_execution_id=None,execution_context=self.context("job-b"),snapshot_store=self.store)
 def test_corrupt_snapshot_is_rejected_on_read(self):
  ref=self.store.put_verified(self.source,allowed_root=self.allowed,artifact_id="tamper")
  blob=self.store.root/ref.storage_key; blob.chmod(0o644); blob.write_bytes(b"tampered")
  with self.assertRaisesRegex(ValueError,"integrity verification"): self.store.get_verified(ref)
 def test_rejects_snapshot_reference_from_another_artifact(self):
  ref1=self.store.put_verified(self.source,allowed_root=self.allowed,artifact_id="asset-one")
  other=self.allowed/"different.bin"; other.write_bytes(b"different content")
  ref2=self.store.put_verified(other,allowed_root=self.allowed,artifact_id="asset-two")
  forged=type(ref1)(artifact_id=ref1.artifact_id,sha256=ref2.sha256,size_bytes=ref2.size_bytes,storage_key=ref2.storage_key,verification_version=ref2.verification_version)
  with self.assertRaisesRegex(ValueError,"does not match stored metadata"): self.store.verify(forged)
if __name__=="__main__": unittest.main()
