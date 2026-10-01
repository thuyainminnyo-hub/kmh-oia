"""Tests for the optimization regression guard."""
import unittest

from src.optimization_regression import OptimizationRegressionGuard


class OptimizationRegressionGuardTests(unittest.TestCase):
    def setUp(self):
        self.guard = OptimizationRegressionGuard()

    def test_higher_is_better_detects_regression(self):
        result = self.guard.evaluate(metric="throughput", baseline=100, observed=90, direction="higher")
        self.assertTrue(result.regression)
        with self.assertRaises(RuntimeError):
            self.guard.require_no_regression(result)

    def test_lower_is_better_detects_regression(self):
        result = self.guard.evaluate(metric="latency_ms", baseline=80, observed=100, direction="lower")
        self.assertTrue(result.regression)

    def test_non_regression_passes_in_both_directions(self):
        higher = self.guard.evaluate(metric="throughput", baseline=100, observed=100, direction="higher")
        lower = self.guard.evaluate(metric="latency_ms", baseline=80, observed=70, direction="lower")
        self.guard.require_no_regression(higher)
        self.guard.require_no_regression(lower)
        self.assertFalse(higher.regression)
        self.assertFalse(lower.regression)

    def test_invalid_inputs_rejected(self):
        for kwargs in (
            dict(metric="", baseline=1, observed=2, direction="higher"),
            dict(metric="x", baseline=float("nan"), observed=2, direction="higher"),
            dict(metric="x", baseline=1, observed=float("inf"), direction="lower"),
            dict(metric="x", baseline=True, observed=2, direction="higher"),
            dict(metric="x", baseline=1, observed=2, direction="sideways"),
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.guard.evaluate(**kwargs)

    def test_validation_cannot_be_bypassed(self):
        with self.assertRaises(RuntimeError):
            self.guard.require_no_regression(None)


if __name__ == "__main__":
    unittest.main()
