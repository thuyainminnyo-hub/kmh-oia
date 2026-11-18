import tempfile
import unittest
import struct
import zlib
from pathlib import Path

from src.production_job import ProductionJob


def valid_png_bytes():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\xff")) + chunk(b"IEND", b"")
from src.production_execution import AdapterResult, ProductionExecutionBridge


class FakeAdapter:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.seen_job = None

    def execute(self, job):
        self.seen_job = job
        if self.error:
            raise self.error
        return self.result


class ProductionExecutionBridgeTests(unittest.TestCase):
    def setUp(self):
        self.job = ProductionJob.create("image", "A studio product photo")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def bridge(self, adapter):
        return ProductionExecutionBridge(adapter, allowed_output_root=self.root)

    def test_success_requires_verified_file_and_moves_to_qa_pending(self):
        artifact = self.root / "image.png"
        artifact.write_bytes(valid_png_bytes())
        adapter = FakeAdapter(AdapterResult(True, str(artifact), provider_execution_id="prompt-abc"))
        result = self.bridge(adapter).execute(self.job)
        self.assertEqual(result.status, "qa_pending")
        self.assertEqual(result.output_path, str(artifact.resolve()))
        self.assertEqual(result.provider_execution_id, "prompt-abc")
        self.assertEqual(result.attempt, 1)
        self.assertEqual(adapter.seen_job.status, "running")

    def test_corrupt_png_fails_integrity_gate(self):
        artifact = self.root / "corrupt.png"
        artifact.write_bytes(b"\x89PNG\r\n\x1a\nnot-a-real-png")
        result = self.bridge(FakeAdapter(AdapterResult(True, str(artifact)))).execute(self.job)
        self.assertEqual(result.status, "failed")
        self.assertIn("image integrity verification failed", result.error_message)

    def test_unsupported_image_format_fails_closed_in_v1(self):
        artifact = self.root / "image.jpg"
        artifact.write_bytes(b"\xff\xd8\xfffake-jpeg")
        result = self.bridge(FakeAdapter(AdapterResult(True, str(artifact)))).execute(self.job)
        self.assertEqual(result.status, "failed")
        self.assertIn("PNG only", result.error_message)

    def test_adapter_failure_fails_closed(self):
        adapter = FakeAdapter(AdapterResult(False, error_message="model unavailable"))
        result = self.bridge(adapter).execute(self.job)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_message, "model unavailable")
        self.assertEqual(result.attempt, 1)

    def test_success_without_path_is_failure(self):
        result = self.bridge(FakeAdapter(AdapterResult(True))).execute(self.job)
        self.assertEqual(result.status, "failed")
        self.assertIn("non-empty string", result.error_message)

    def test_nonexistent_artifact_is_failure(self):
        result = self.bridge(
            FakeAdapter(AdapterResult(True, str(self.root / "missing.png")))
        ).execute(self.job)
        self.assertEqual(result.status, "failed")
        self.assertIn("does not exist", result.error_message)

    def test_artifact_outside_allowed_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            artifact = Path(outside) / "outside.png"
            artifact.write_bytes(b"not allowed")
            result = self.bridge(
                FakeAdapter(AdapterResult(True, str(artifact)))
            ).execute(self.job)
        self.assertEqual(result.status, "failed")
        self.assertIn("escapes", result.error_message)

    def test_empty_artifact_is_rejected(self):
        artifact = self.root / "empty.png"
        artifact.write_bytes(b"")
        result = self.bridge(
            FakeAdapter(AdapterResult(True, str(artifact)))
        ).execute(self.job)
        self.assertEqual(result.status, "failed")
        self.assertIn("empty", result.error_message)

    def test_invalid_adapter_result_fails_closed(self):
        result = self.bridge(FakeAdapter(result="success")).execute(self.job)
        self.assertEqual(result.status, "failed")
        self.assertIn("invalid result type", result.error_message)

    def test_adapter_exception_is_captured(self):
        result = self.bridge(
            FakeAdapter(error=RuntimeError("simulated crash"))
        ).execute(self.job)
        self.assertEqual(result.status, "failed")
        self.assertIn("simulated crash", result.error_message)

    def test_only_queued_jobs_can_execute(self):
        running = ProductionJob(
            job_id=self.job.job_id, asset_type="image",
            prompt="A studio product photo", status="running",
        )
        with self.assertRaisesRegex(ValueError, "queued"):
            self.bridge(FakeAdapter(AdapterResult(True))).execute(running)


if __name__ == "__main__":
    unittest.main()
