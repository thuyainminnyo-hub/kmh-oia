import tempfile
import unittest
from pathlib import Path

from src.production_audit import JsonlProductionAuditSink
from src.production_execution import AdapterResult, ProductionExecutionBridge
from src.production_job import ProductionJob
from src.production_pipeline import execute_with_evidence


class FakeAdapter:
    def __init__(self, result):
        self.result = result

    def execute(self, job):
        return self.result


class ProductionPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.job = ProductionJob.create("image", "Synthetic test prompt")
        self.audit = JsonlProductionAuditSink(self.root / "audit.jsonl")

    def test_executes_verifies_hashes_and_records_audit(self):
        output = self.root / "synthetic.png"
        output.write_bytes(b"synthetic image bytes")
        bridge = ProductionExecutionBridge(
            FakeAdapter(AdapterResult(True, str(output))),
            allowed_output_root=self.root,
        )
        result = execute_with_evidence(
            self.job, bridge=bridge, adapter_name="fake",
            allowed_output_root=self.root, audit_sink=self.audit,
            provider_execution_id="synthetic-prompt-id",
        )
        self.assertEqual(result.job.status, "qa_pending")
        self.assertIsNotNone(result.evidence)
        self.assertEqual(result.evidence.qa_decision, "pending")
        events = self.audit.verify_chain()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "evidence_created")
        self.assertEqual(events[0]["payload"]["output_sha256"], result.evidence.output_sha256)

    def test_failed_execution_does_not_create_evidence(self):
        bridge = ProductionExecutionBridge(
            FakeAdapter(AdapterResult(False, error_message="simulated provider failure")),
            allowed_output_root=self.root,
        )
        result = execute_with_evidence(
            self.job, bridge=bridge, adapter_name="fake",
            allowed_output_root=self.root, audit_sink=self.audit,
        )
        self.assertEqual(result.job.status, "failed")
        self.assertIsNone(result.evidence)
        self.assertEqual(self.audit.verify_chain(), [])

    def test_audit_failure_fails_closed_after_output_verification(self):
        output = self.root / "synthetic.png"
        output.write_bytes(b"synthetic image bytes")
        bridge = ProductionExecutionBridge(
            FakeAdapter(AdapterResult(True, str(output))),
            allowed_output_root=self.root,
        )
        bad_sink = JsonlProductionAuditSink(self.root / "bad.jsonl")
        bad_sink.path.write_text("{broken json\n", encoding="utf-8")
        result = execute_with_evidence(
            self.job, bridge=bridge, adapter_name="fake",
            allowed_output_root=self.root, audit_sink=bad_sink,
        )
        self.assertEqual(result.job.status, "failed")
        self.assertIn("evidence/audit recording failed", result.job.error_message)
        self.assertIsNone(result.evidence)


if __name__ == "__main__":
    unittest.main()
