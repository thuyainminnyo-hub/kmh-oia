import unittest

from src.production_job import ProductionJob


class ProductionJobContractTests(unittest.TestCase):
    def test_create_makes_queued_job_with_unique_ids(self):
        first = ProductionJob.create("image", "A product photo")
        second = ProductionJob.create("video", "A 10-second product clip")
        self.assertNotEqual(first.job_id, second.job_id)
        self.assertEqual(first.status, "queued")
        self.assertEqual(second.asset_type, "video")
        self.assertEqual(first.attempt, 0)

    def test_rejects_blank_job_id_or_prompt(self):
        with self.assertRaisesRegex(ValueError, "job_id"):
            ProductionJob(job_id=" ", asset_type="image", prompt="valid")
        with self.assertRaisesRegex(ValueError, "prompt"):
            ProductionJob(job_id="job-1", asset_type="image", prompt=" ")

    def test_rejects_unknown_asset_type_and_status(self):
        with self.assertRaisesRegex(ValueError, "asset_type"):
            ProductionJob(job_id="job-1", asset_type="audio", prompt="valid")
        with self.assertRaisesRegex(ValueError, "status"):
            ProductionJob(job_id="job-1", asset_type="image", prompt="valid", status="done")

    def test_rejects_negative_attempt_and_naive_timestamp(self):
        with self.assertRaisesRegex(ValueError, "attempt"):
            ProductionJob(job_id="job-1", asset_type="image", prompt="valid", attempt=-1)
        with self.assertRaisesRegex(ValueError, "timezone"):
            ProductionJob(
                job_id="job-1",
                asset_type="image",
                prompt="valid",
                created_at="2026-10-29T12:00:00",
            )

    def test_approved_job_requires_output_path(self):
        with self.assertRaisesRegex(ValueError, "output_path"):
            ProductionJob(
                job_id="job-1",
                asset_type="image",
                prompt="valid",
                status="approved",
            )
        job = ProductionJob(
            job_id="job-1",
            asset_type="image",
            prompt="valid",
            status="approved",
            output_path="artifacts/job-1.png",
        )
        self.assertEqual(job.output_path, "artifacts/job-1.png")


if __name__ == "__main__":
    unittest.main()
