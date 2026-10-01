"""Tests for optimization evidence comparison."""
import unittest

from src.optimization_evidence import OptimizationEvidenceController


class OptimizationEvidenceControllerTests(unittest.TestCase):
    def setUp(self):
        self.controller = OptimizationEvidenceController()

    def test_higher_is_better_comparison(self):
        result = self.controller.compare(
            metric="throughput", before=100, after=120, direction="higher"
        )
        self.assertTrue(result.improved)
        self.assertEqual(result.delta, 20.0)

    def test_lower_is_better_comparison(self):
        result = self.controller.compare(
            metric="latency_ms", before=120, after=90, direction="lower"
        )
        self.assertTrue(result.improved)
        self.assertEqual(result.delta, -30.0)

    def test_no_change_is_not_improvement(self):
        result = self.controller.compare(
            metric="error_rate", before=2, after=2, direction="lower"
        )
        self.assertFalse(result.improved)
        self.assertEqual(result.delta, 0.0)

    def test_invalid_measurements_and_direction_rejected(self):
        with self.assertRaises(ValueError):
            self.controller.compare(metric="", before=1, after=2, direction="higher")
        with self.assertRaises(ValueError):
            self.controller.compare(metric="x", before=True, after=2, direction="higher")
        with self.assertRaises(ValueError):
            self.controller.compare(metric="x", before=1, after=2, direction="same")


if __name__ == "__main__":
    unittest.main()
