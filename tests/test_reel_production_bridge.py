import unittest

from src.reel_production_bridge import ReelProductionJob, execute_reel_job


class ReelProductionBridgeTests(unittest.TestCase):
    def test_day2_job_produces_traceable_runtime_result(self):
        result = execute_reel_job(
            ReelProductionJob(
                run_id="KMH-REEL-DAY02-RUN01",
                topic="ကား၊ ဆိုင်ကယ် မောင်းနှင်ရာမှာ သိထားသင့်တဲ့အချက်များ",
            )
        )
        self.assertEqual(result.run_id, "KMH-REEL-DAY02-RUN01")
        self.assertIn("KMH-REEL-DAY02-RUN01", result.response)
        self.assertIn("input_gateway", result.stages)
        self.assertIn("trace", result.stages)
        self.assertGreaterEqual(result.trace_event_count, 10)

    def test_invalid_duration_is_blocked_before_runtime(self):
        with self.assertRaises(ValueError):
            execute_reel_job(
                ReelProductionJob(
                    run_id="KMH-REEL-DAY02-RUN01",
                    topic="road safety",
                    duration_seconds=120,
                )
            )

    def test_invalid_aspect_ratio_is_blocked_before_runtime(self):
        with self.assertRaises(ValueError):
            execute_reel_job(
                ReelProductionJob(
                    run_id="KMH-REEL-DAY02-RUN01",
                    topic="road safety",
                    aspect_ratio="16:9",
                )
            )


if __name__ == "__main__":
    unittest.main()
