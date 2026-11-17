import json,tempfile,unittest
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor
from pathlib import Path
from src.execution_identity import ExecutionIdentity,ExecutionIdentityContext
from src.production_audit import JsonlProductionAuditSink
from src.production_evidence import ProductionEvidence
from src.verified_snapshot_store import VerifiedArtifactStore
def _process_qa_decision(args):
 path,digest,index=args
 sink=JsonlProductionAuditSink(path)
 try:
  sink.record_qa_decision(job_id="job-1",output_sha256=digest,decision="approved" if index%2==0 else "rejected",reviewer_id=f"process-reviewer-{index}")
  return "recorded"
 except ValueError as exc:
  if "already recorded" in str(exc): return "rejected"
  raise

class JsonlProductionAuditSinkTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); root=Path(self.temp.name)
  out=root/"out"; out.mkdir(); file=out/"image.png"; file.write_bytes(b"image fixture")
  store=VerifiedArtifactStore(root/"store"); snap=store.put_verified(file,allowed_root=out,artifact_id="job-job-1")
  ctx=ExecutionIdentityContext(ExecutionIdentity("a","i","prod","s"),"cmd","exec","job-1")
  self.path=root/"audit.jsonl"; self.sink=JsonlProductionAuditSink(self.path)
  self.evidence=ProductionEvidence.from_snapshot(job_id="job-1",adapter_name="fake",output_path=str(file),snapshot=snap,elapsed_ms=10,provider_execution_id="prompt-1",context=ctx)
 def test_records_evidence_and_qa_decision_in_hash_chain(self):
  first=self.sink.record_evidence(self.evidence); second=self.sink.record_qa_decision(job_id="job-1",output_sha256=self.evidence.output_sha256,decision="approved",reviewer_id="reviewer-1")
  events=self.sink.verify_chain(); self.assertEqual(len(events),2); self.assertEqual(events[0]["event_type"],"evidence_created")
  self.assertEqual(events[1]["event_type"],"qa_decision_recorded"); self.assertEqual(second["previous_hash"],first["event_hash"])
  self.assertEqual(events[0]["payload"]["snapshot_reference"],self.evidence.snapshot_reference)
 def test_detects_event_tampering(self):
  self.sink.record_evidence(self.evidence); event=json.loads(self.path.read_text(encoding="utf-8"))
  event["payload"]["output_size_bytes"]=999; self.path.write_text(json.dumps(event)+"\n",encoding="utf-8")
  with self.assertRaisesRegex(ValueError,"hash mismatch"): self.sink.verify_chain()
 def test_rejects_invalid_qa_decision(self):
  with self.assertRaisesRegex(ValueError,"QA decision"): self.sink.record_qa_decision(job_id="job",output_sha256="a"*64,decision="pending",reviewer_id="reviewer")
 def test_qa_decision_binds_to_matching_evidence_event(self):
  evidence_event=self.sink.record_evidence(self.evidence)
  qa_event=self.sink.record_qa_decision(job_id="job-1",output_sha256=self.evidence.output_sha256,decision="approved",reviewer_id="reviewer")
  self.assertEqual(qa_event["payload"]["evidence_event_hash"],evidence_event["event_hash"])
  self.assertEqual(qa_event["payload"]["snapshot_reference"],self.evidence.snapshot_reference)
  self.assertEqual(qa_event["payload"]["execution_id"],self.evidence.execution_id)
  self.assertEqual(qa_event["payload"]["identity_key"],self.evidence.identity_key)
 def test_rejects_second_conflicting_qa_decision_for_same_evidence(self):
  self.sink.record_evidence(self.evidence)
  self.sink.record_qa_decision(job_id="job-1",output_sha256=self.evidence.output_sha256,decision="approved",reviewer_id="reviewer-1")
  with self.assertRaisesRegex(ValueError,"already recorded"):
   self.sink.record_qa_decision(job_id="job-1",output_sha256=self.evidence.output_sha256,decision="rejected",reviewer_id="reviewer-2")
 def test_concurrent_qa_decisions_are_serialized(self):
  self.sink.record_evidence(self.evidence)
  def decide(index):
   try:
    self.sink.record_qa_decision(job_id="job-1",output_sha256=self.evidence.output_sha256,decision="approved" if index%2==0 else "rejected",reviewer_id=f"reviewer-{index}")
    return "recorded"
   except ValueError as exc:
    if "already recorded" in str(exc): return "rejected"
    raise
  with ThreadPoolExecutor(max_workers=8) as pool:
   outcomes=list(pool.map(decide,range(8)))
  self.assertEqual(outcomes.count("recorded"),1)
  events=self.sink.verify_chain()
  self.assertEqual(sum(event["event_type"]=="qa_decision_recorded" for event in events),1)
 def test_cross_process_qa_decisions_are_serialized(self):
  self.sink.record_evidence(self.evidence)
  args=[(str(self.path),self.evidence.output_sha256,index) for index in range(4)]
  with ProcessPoolExecutor(max_workers=4) as pool:
   outcomes=list(pool.map(_process_qa_decision,args))
  self.assertEqual(outcomes.count("recorded"),1)
  events=self.sink.verify_chain()
  self.assertEqual(sum(event["event_type"]=="qa_decision_recorded" for event in events),1)
 def test_qa_decision_rejects_without_prior_evidence(self):
  with self.assertRaisesRegex(ValueError,"prior evidence event"):
   self.sink.record_qa_decision(job_id="job-1",output_sha256=self.evidence.output_sha256,decision="approved",reviewer_id="reviewer")
 def test_qa_decision_rejects_wrong_digest(self):
  self.sink.record_evidence(self.evidence)
  with self.assertRaisesRegex(ValueError,"prior evidence event"):
   self.sink.record_qa_decision(job_id="job-1",output_sha256="0"*64,decision="approved",reviewer_id="reviewer")
 def test_rejects_blank_reviewer(self):
  with self.assertRaisesRegex(ValueError,"reviewer_id"): self.sink.record_qa_decision(job_id="job",output_sha256="a"*64,decision="approved",reviewer_id=" ")
if __name__=="__main__": unittest.main()
