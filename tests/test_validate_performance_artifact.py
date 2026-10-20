import unittest

from scripts.validate_performance_artifact import validate_performance_payload


class PerformanceArtifactValidationTests(unittest.TestCase):
    def test_accepts_valid_performance_report(self):
        payload = {
            "iterations": 50,
            "min_ms": 0.2,
            "median_ms": 0.4,
            "mean_ms": 0.42,
            "max_ms": 0.9,
        }
        self.assertEqual(validate_performance_payload(payload), [])

    def test_rejects_non_object_payload(self):
        self.assertIn(
            "top-level performance report must be a JSON object",
            validate_performance_payload([1, 2, 3]),
        )

    def test_rejects_missing_metric(self):
        payload = {"iterations": 10, "min_ms": 1, "median_ms": 2, "mean_ms": 2}
        errors = validate_performance_payload(payload)
        self.assertTrue(any("max_ms must be a number" in error for error in errors))

    def test_rejects_invalid_iteration_count_and_boolean_metrics(self):
        payload = {
            "iterations": True,
            "min_ms": False,
            "median_ms": 2,
            "mean_ms": 2,
            "max_ms": 3,
        }
        errors = validate_performance_payload(payload)
        self.assertTrue(any("iterations must be an integer" in error for error in errors))
        self.assertTrue(any("min_ms must be a number" in error for error in errors))

    def test_rejects_nonfinite_or_negative_metrics(self):
        payload = {
            "iterations": 10,
            "min_ms": -1,
            "median_ms": 2,
            "mean_ms": float("nan"),
            "max_ms": float("inf"),
        }
        errors = validate_performance_payload(payload)
        self.assertTrue(any("min_ms must be finite" in error for error in errors))
        self.assertTrue(any("mean_ms must be finite" in error for error in errors))
        self.assertTrue(any("max_ms must be finite" in error for error in errors))

    def test_rejects_inconsistent_metric_order(self):
        payload = {
            "iterations": 10,
            "min_ms": 1,
            "median_ms": 5,
            "mean_ms": 2,
            "max_ms": 4,
        }
        errors = validate_performance_payload(payload)
        self.assertTrue(any("median_ms must be less than or equal to max_ms" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
