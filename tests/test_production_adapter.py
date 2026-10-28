import unittest

from src.production_adapter import ExecutionResult, FakeProductionAdapter
from src.production_job import ProductionJob


class ProductionAdapterTests(unittest.TestCase):
    def setUp(self):
        self.job = ProductionJob.create(asset_type="image", prompt="test prompt")

    def test_fake_adapter_returns_virtual_output_reference(self):
        result = FakeProductionAdapter().execute(self.job)

        self.assertTrue(result.success)
        self.assertEqual(result.adapter_name, "fake")
        self.assertEqual(
            result.output_ref, f"fake://outputs/{self.job.job_id}.image"
        )
        self.assertIsNone(result.error_message)

    def test_fake_adapter_can_model_execution_failure(self):
        result = FakeProductionAdapter(fail_with="simulated failure").execute(self.job)

        self.assertFalse(result.success)
        self.assertIsNone(result.output_ref)
        self.assertEqual(result.error_message, "simulated failure")

    def test_adapter_rejects_wrong_job_type(self):
        with self.assertRaises(TypeError):
            FakeProductionAdapter().execute("not a job")

    def test_success_requires_output_reference(self):
        with self.assertRaises(ValueError):
            ExecutionResult(success=True, adapter_name="test")

    def test_failure_requires_error_message(self):
        with self.assertRaises(ValueError):
            ExecutionResult(success=False, adapter_name="test")

    def test_result_rejects_success_with_error(self):
        with self.assertRaises(ValueError):
            ExecutionResult(
                success=True,
                adapter_name="test",
                output_ref="fake://output",
                error_message="contradictory",
            )


if __name__ == "__main__":
    unittest.main()
