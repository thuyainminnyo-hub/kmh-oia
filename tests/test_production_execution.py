import tempfile
import unittest
from pathlib import Path

from src.production_job import ProductionJob
from src.production_execution import (
    AdapterResult,
    ProductionExecutionBridge,
)


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

    def test_success_requires_real_file_and_moves_to_qa_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "image.png"
            artifact.write_bytes(b"fake-image-fixture")
            adapter = FakeAdapter(AdapterResult(True, str(artifact)))
            result = ProductionExecutionBridge(adapter).execute(self.job)
        self.assertEqual(result.status, "qa_pending")
        self.assertEqual(result.output_path, str(artifact))
        self.assertEqual(result.attempt, 1)
        self.assertEqual(adapter.seen_job.status, "running")

    def test_adapter_failure_fails_closed(self):
        adapter = FakeAdapter(AdapterResult(False, error_message="model unavailable"))
        result = ProductionExecutionBridge(adapter).execute(self.job)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_message, "model unavailable")
        self.assertEqual(result.attempt, 1)

    def test_success_without_path_is_failure(self):
        adapter = FakeAdapter(AdapterResult(True))
        result = ProductionExecutionBridge(adapter).execute(self.job)
        self.assertEqual(result.status, "failed")
        self.assertIn("without an output path", result.error_message)

    def test_nonexistent_artifact_is_failure(self):
        adapter = FakeAdapter(AdapterResult(True, "/not/a/real/artifact.png"))
        result = ProductionExecutionBridge(adapter).execute(self.job)
        self.assertEqual(result.status, "failed")
        self.assertIn("does not exist", result.error_message)

    def test_adapter_exception_is_captured(self):
        adapter = FakeAdapter(error=RuntimeError("simulated crash"))
        result = ProductionExecutionBridge(adapter).execute(self.job)
        self.assertEqual(result.status, "failed")
        self.assertIn("simulated crash", result.error_message)

    def test_only_queued_jobs_can_execute(self):
        running = ProductionJob(
            job_id=self.job.job_id,
            asset_type="image",
            prompt="A studio product photo",
            status="running",
        )
        with self.assertRaisesRegex(ValueError, "queued"):
            ProductionExecutionBridge(FakeAdapter(AdapterResult(True))).execute(running)


if __name__ == "__main__":
    unittest.main()
