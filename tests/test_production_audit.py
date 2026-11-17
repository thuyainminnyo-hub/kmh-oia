import json
import tempfile
import unittest
from pathlib import Path
from src.execution_identity import ExecutionIdentity, ExecutionIdentityContext
from src.production_audit import JsonlProductionAuditSink
from src.production_evidence import ProductionEvidence
from src.verified_snapshot_store import VerifiedArtifactStore

class JsonlProductionAuditSinkTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name); outputs=root/"outputs"; outputs.mkdir()
        output=outputs/"image.png"; output.write_bytes(b"image fixture")
        store=VerifiedArtifactStore(root/"store")
        snapshot=store.put_verified(output,allowed_root=outputs,artifact_id="audit-artifact")
        context=ExecutionIdentityContext(ExecutionIdentity("a","i","prod","s"),"cmd","exec")
        self.path=root/"audit.jsonl"; self.sink=JsonlProductionAuditSink(self.path)
        self.evidence=ProductionEvidence.from_snapshot(job_id="job-1",adapter_name="fake",output_path=str(output),
            snapshot=snapshot,elapsed_ms=10,provider_execution_id="prompt-1",context=context)
    def test_records_evidence_and_qa_decision_in_hash_chain(self):
        first=self.sink.record_evidence(self.evidence)
        second=self.sink.record_qa_decision(job_id="job-1",output_sha256=self.evidence.output_sha256,
            decision="approved",reviewer_id="reviewer-1")
        events=self.sink.verify_chain(); self.assertEqual(len(events),2)
        self.assertEqual(events[0]["event_type"],"evidence_created")
        self.assertEqual(events[1]["event_type"],"qa_decision_recorded")
        self.assertEqual(second["previous_hash"],first["event_hash"])
        self.assertEqual(events[0]["payload"]["snapshot_reference"],self.evidence.snapshot_reference)
    def test_detects_event_tampering(self):
        self.sink.record_evidence(self.evidence); event=json.loads(self.path.read_text(encoding="utf-8"))
        event["payload"]["output_size_bytes"]=999; self.path.write_text(json.dumps(event)+"\\n",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"hash mismatch"): self.sink.verify_chain()
    def test_rejects_invalid_qa_decision(self):
        with self.assertRaisesRegex(ValueError,"QA decision"):
            self.sink.record_qa_decision(job_id="job",output_sha256="a"*64,decision="pending",reviewer_id="reviewer")
    def test_rejects_blank_reviewer(self):
        with self.assertRaisesRegex(ValueError,"reviewer_id"):
            self.sink.record_qa_decision(job_id="job",output_sha256="a"*64,decision="approved",reviewer_id=" ")
if __name__=="__main__": unittest.main()
