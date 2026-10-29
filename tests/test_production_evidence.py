import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.production_evidence import ProductionEvidence


class ProductionEvidenceTests(unittest.TestCase):
    def test_builds_manifest_with_sha256_and_pending_qa(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "synthetic.png")
            payload = b"synthetic image fixture"
            path.write_bytes(payload)
            evidence = ProductionEvidence.from_output(
                job_id="job-1",
                adapter_name="fake",
                output_path=path,
                elapsed_ms=125,
                provider_execution_id="prompt-123",
            )
            self.assertEqual(evidence.output_sha256, hashlib.sha256(payload).hexdigest())
            self.assertEqual(evidence.output_size_bytes, len(payload))
            self.assertEqual(evidence.qa_decision, "pending")
            self.assertEqual(evidence.provider_execution_id, "prompt-123")

    def test_rejects_empty_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "empty.png")
            path.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "must not be empty"):
                ProductionEvidence.from_output(
                    job_id="job-1", adapter_name="fake", output_path=path, elapsed_ms=0
                )

    def test_rejects_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                ProductionEvidence.from_output(
                    job_id="job-1", adapter_name="fake",
                    output_path=Path(tmp, "missing.png"), elapsed_ms=0
                )

    def test_json_is_stable_and_does_not_auto_approve(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "output.png")
            path.write_bytes(b"pixels")
            evidence = ProductionEvidence.from_output(
                job_id="job-2", adapter_name="comfyui-local",
                output_path=path, elapsed_ms=999, provider_execution_id="prompt-abc"
            )
            parsed = json.loads(evidence.to_json())
            self.assertEqual(parsed["qa_decision"], "pending")
            self.assertEqual(parsed["job_id"], "job-2")

    def test_invalid_digest_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            ProductionEvidence(
                job_id="job", adapter_name="fake", output_path="/tmp/out",
                output_sha256="bad", output_size_bytes=1, elapsed_ms=0,
                provider_execution_id=None
            )


if __name__ == "__main__":
    unittest.main()
