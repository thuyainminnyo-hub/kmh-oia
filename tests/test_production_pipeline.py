import tempfile,unittest
from pathlib import Path
from src.execution_identity import ExecutionIdentity
from src.production_audit import JsonlProductionAuditSink
from src.production_execution import AdapterResult,ProductionExecutionBridge
from src.production_job import ProductionJob
from src.production_pipeline import execute_with_evidence
from src.verified_snapshot_store import VerifiedArtifactStore,VerifiedSnapshot
class FakeAdapter:
 def __init__(self,result): self.result=result
 def execute(self,job): return self.result
class ProductionPipelineTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.root=Path(self.temp.name)
  self.job=ProductionJob.create("image","Synthetic test prompt",execution_identity=ExecutionIdentity("a","i","prod","s"))
  self.audit=JsonlProductionAuditSink(self.root/"audit.jsonl"); self.store=VerifiedArtifactStore(self.root/"snapshots")
 def run_pipeline(self,adapter,**kwargs):
  return execute_with_evidence(self.job,bridge=ProductionExecutionBridge(adapter,allowed_output_root=self.root),adapter_name="fake",allowed_output_root=self.root,audit_sink=self.audit,snapshot_store=self.store,**kwargs)
 def test_executes_snapshots_hashes_and_records_audit(self):
  output=self.root/"synthetic.png"; output.write_bytes(b"synthetic image bytes")
  result=self.run_pipeline(FakeAdapter(AdapterResult(True,str(output),provider_execution_id="actual-id")))
  self.assertEqual(result.job.status,"qa_pending"); self.assertIsNotNone(result.evidence); self.assertEqual(result.evidence.qa_decision,"pending")
  ref=VerifiedSnapshot(result.evidence.artifact_id,result.evidence.output_sha256,result.evidence.output_size_bytes,result.evidence.snapshot_reference,result.evidence.verification_version)
  self.assertEqual(self.store.get_verified(ref),b"synthetic image bytes")
  self.assertEqual(self.audit.verify_chain()[0]["payload"]["execution_id"],result.evidence.execution_id)
 def test_failed_execution_does_not_create_evidence(self):
  result=self.run_pipeline(FakeAdapter(AdapterResult(False,error_message="simulated provider failure")))
  self.assertEqual(result.job.status,"failed"); self.assertIsNone(result.evidence); self.assertEqual(self.audit.verify_chain(),[])
 def test_audit_failure_fails_closed_after_output_verification(self):
  output=self.root/"synthetic.png"; output.write_bytes(b"synthetic image bytes")
  bad=JsonlProductionAuditSink(self.root/"bad.jsonl"); bad.path.write_text("{broken json",encoding="utf-8")
  result=execute_with_evidence(self.job,bridge=ProductionExecutionBridge(FakeAdapter(AdapterResult(True,str(output))),allowed_output_root=self.root),adapter_name="fake",allowed_output_root=self.root,audit_sink=bad,snapshot_store=self.store)
  self.assertEqual(result.job.status,"failed"); self.assertIsNone(result.evidence)
if __name__=="__main__": unittest.main()
