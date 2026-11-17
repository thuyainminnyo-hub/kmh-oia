import tempfile,unittest
from pathlib import Path
from src.execution_identity import ExecutionIdentity,ExecutionIdentityContext
from src.production_evidence_gate import create_verified_evidence
from src.production_audit import JsonlProductionAuditSink
from src.verified_snapshot_store import VerifiedArtifactStore
class ProductionEvidenceGateTests(unittest.TestCase):
 def setup_case(self):
  tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup); root=Path(tmp.name); output=root/"image.bin"; output.write_bytes(b"synthetic output")
  context=ExecutionIdentityContext(ExecutionIdentity("a","i","prod","s"),"cmd","exec","job-1")
  return root,output,context,VerifiedArtifactStore(root/"snapshots")
 def test_creates_snapshot_bound_pending_evidence(self):
  root,output,context,store=self.setup_case()
  evidence=create_verified_evidence(job_id="job-1",adapter_name="fake",output_path=str(output),allowed_output_root=root,elapsed_ms=100,provider_execution_id="provider-1",execution_context=context,snapshot_store=store)
  self.assertEqual(evidence.qa_decision,"pending"); self.assertEqual(evidence.execution_id,"exec"); self.assertEqual(evidence.output_size_bytes,len(b"synthetic output"))
 def test_records_provenance_to_audit_sink(self):
  root,output,context,store=self.setup_case(); sink=JsonlProductionAuditSink(root/"audit.jsonl")
  evidence=create_verified_evidence(job_id="job-1",adapter_name="fake",output_path=str(output),allowed_output_root=root,elapsed_ms=20,provider_execution_id="provider-audit",execution_context=context,snapshot_store=store,audit_sink=sink)
  events=sink.verify_chain(); self.assertEqual(len(events),1); self.assertEqual(events[0]["payload"]["snapshot_reference"],evidence.snapshot_reference)
  self.assertEqual(events[0]["payload"]["identity_key"],evidence.identity_key)
 def test_records_absolute_lexical_path_for_relative_output(self):
  root,output,context,store=self.setup_case()
  evidence=create_verified_evidence(job_id="job-1",adapter_name="fake",output_path="image.bin",allowed_output_root=root,elapsed_ms=10,provider_execution_id="provider-relative",execution_context=context,snapshot_store=store)
  self.assertEqual(evidence.output_path,str(output))

 def test_does_not_resolve_source_symlink_in_recorded_path(self):
  root,output,context,store=self.setup_case()
  link=root/"image-link.bin"; link.symlink_to(output)
  with self.assertRaises(ValueError):
   create_verified_evidence(job_id="job-1",adapter_name="fake",output_path=str(link),allowed_output_root=root,elapsed_ms=10,provider_execution_id="provider-link",execution_context=context,snapshot_store=store)

 def test_rejects_missing_output(self):
  root,output,context,store=self.setup_case(); output.unlink()
  with self.assertRaises((ValueError,FileNotFoundError)):
   create_verified_evidence(job_id="job-1",adapter_name="fake",output_path=str(output),allowed_output_root=root,elapsed_ms=0,provider_execution_id=None,execution_context=context,snapshot_store=store)
 def test_rejects_output_outside_allowed_root(self):
  root,output,context,store=self.setup_case()
  with tempfile.TemporaryDirectory() as outside:
   other=Path(outside)/"other.bin"; other.write_bytes(b"outside")
   with self.assertRaises(ValueError):
    create_verified_evidence(job_id="job-1",adapter_name="fake",output_path=str(other),allowed_output_root=root,elapsed_ms=1,provider_execution_id=None,execution_context=context,snapshot_store=store)
if __name__=="__main__": unittest.main()
