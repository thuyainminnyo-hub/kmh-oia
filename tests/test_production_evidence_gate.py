import tempfile
import unittest
from pathlib import Path

from src.production_evidence_gate import create_verified_evidence
from src.production_audit import JsonlProductionAuditSink
from src.verified_snapshot_store import VerifiedArtifactStore
import hashlib


class ProductionEvidenceGateTests(unittest.TestCase):
    def test_requires_output_inside_allowed_root_and_creates_pending_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "image.png"
            output.write_bytes(b"synthetic output")
            evidence = create_verified_evidence(
                job_id="job-1", adapter_name="fake", output_path=str(output),
                allowed_output_root=root, elapsed_ms=100,
                provider_execution_id="prompt-1",
            )
            self.assertEqual(evidence.qa_decision, "pending")
            self.assertEqual(evidence.provider_execution_id, "prompt-1")
            self.assertEqual(evidence.output_size_bytes, len(b"synthetic output"))

    def test_records_evidence_to_optional_audit_sink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "image.png"
            output.write_bytes(b"synthetic output")
            sink = JsonlProductionAuditSink(root / "audit.jsonl")
            evidence = create_verified_evidence(
                job_id="job-audit", adapter_name="fake", output_path=str(output),
                allowed_output_root=root, elapsed_ms=20,
                provider_execution_id="prompt-audit", audit_sink=sink,
            )
            events = sink.verify_chain()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["event_type"], "evidence_created")
            self.assertEqual(events[0]["payload"]["output_sha256"], evidence.output_sha256)
            self.assertEqual(evidence.qa_decision, "pending")

    def test_verified_png_bytes_are_bound_to_immutable_snapshot_before_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "image.png"
            output.write_bytes(b"mutable path contents may later change")
            payload = b"the exact PNG bytes already validated upstream"
            store = VerifiedArtifactStore(root / "snapshots")
            sink = JsonlProductionAuditSink(root / "audit.jsonl")
            evidence = create_verified_evidence(
                job_id="job-snapshot", adapter_name="fake", output_path=str(output),
                allowed_output_root=root, elapsed_ms=10,
                provider_execution_id="provider-1", audit_sink=sink,
                verified_bytes=payload,
                expected_sha256=hashlib.sha256(payload).hexdigest(),
                expected_size_bytes=len(payload), snapshot_store=store,
            )
            self.assertEqual(evidence.output_sha256, hashlib.sha256(payload).hexdigest())
            self.assertTrue(evidence.snapshot_reference.startswith("sha256/"))
            self.assertEqual(evidence.verification_version, "verified-bytes-v1")
            events = sink.verify_chain()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["payload"]["snapshot_reference"], evidence.snapshot_reference)
            self.assertEqual(events[0]["payload"]["output_sha256"], evidence.output_sha256)

    def test_verified_payload_digest_mismatch_creates_no_evidence_or_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = b"validated original"
            store = VerifiedArtifactStore(root / "snapshots")
            sink = JsonlProductionAuditSink(root / "audit.jsonl")
            with self.assertRaisesRegex(ValueError, "does not match PNG integrity"):
                create_verified_evidence(
                    job_id="job-mismatch", adapter_name="fake", output_path=str(root / "image.png"),
                    allowed_output_root=root, elapsed_ms=10, audit_sink=sink,
                    verified_bytes=b"substituted payload",
                    expected_sha256=hashlib.sha256(payload).hexdigest(),
                    expected_size_bytes=len(payload), snapshot_store=store,
                )
            self.assertEqual(sink.verify_chain(), [])

    def test_rejects_missing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "output verification failed"):
                create_verified_evidence(
                    job_id="job-2", adapter_name="fake",
                    output_path=str(Path(tmp) / "missing.png"),
                    allowed_output_root=tmp, elapsed_ms=0,
                )

    def test_rejects_output_outside_root(self):
        with tempfile.TemporaryDirectory() as allowed, tempfile.TemporaryDirectory() as outside:
            path = Path(outside) / "other.png"
            path.write_bytes(b"outside")
            with self.assertRaisesRegex(ValueError, "output verification failed"):
                create_verified_evidence(
                    job_id="job-3", adapter_name="fake", output_path=str(path),
                    allowed_output_root=allowed, elapsed_ms=1,
                )


if __name__ == "__main__":
    unittest.main()
