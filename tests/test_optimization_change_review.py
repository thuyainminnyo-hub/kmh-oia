"""Tests for the optimization change review gate."""
import unittest

from src.optimization_regression import OptimizationRegressionGuard
from src.optimization_change_review import OptimizationChangeReviewGate


class OptimizationChangeReviewGateTests(unittest.TestCase):
    def setUp(self):
        self.guard = OptimizationRegressionGuard()
        self.gate = OptimizationChangeReviewGate()
        self.comparison = self.guard.evaluate(
            metric="latency_ms", baseline=100, observed=90, direction="lower"
        )

    def test_requires_change_and_validated_comparison(self):
        with self.assertRaises(ValueError):
            self.gate.prepare(change_id="", comparison=self.comparison)
        with self.assertRaises(ValueError):
            self.gate.prepare(change_id="C-1", comparison=None)

    def test_regression_blocks_review(self):
        regression = self.guard.evaluate(
            metric="latency_ms", baseline=90, observed=100, direction="lower"
        )
        state = self.gate.prepare(change_id="C-1", comparison=regression)
        self.assertEqual(state.phase, "blocked")
        with self.assertRaises(RuntimeError):
            self.gate.review(state, reviewer="operator", accepted=True)

    def test_explicit_acceptance_required(self):
        state = self.gate.prepare(change_id="C-1", comparison=self.comparison)
        with self.assertRaises(RuntimeError):
            self.gate.require_accepted(state)
        accepted = self.gate.review(state, reviewer="reviewer-1", accepted=True)
        self.gate.require_accepted(accepted)
        self.assertEqual(accepted.reviewer, "reviewer-1")

    def test_rejection_and_invalid_review(self):
        state = self.gate.prepare(change_id="C-2", comparison=self.comparison)
        with self.assertRaises(ValueError):
            self.gate.review(state, reviewer="", accepted=True)
        with self.assertRaises(ValueError):
            self.gate.review(state, reviewer="reviewer", accepted="yes")
        rejected = self.gate.review(state, reviewer="reviewer", accepted=False)
        self.assertEqual(rejected.phase, "rejected")
        with self.assertRaises(RuntimeError):
            self.gate.require_accepted(rejected)

    def test_review_cannot_be_repeated(self):
        state = self.gate.prepare(change_id="C-3", comparison=self.comparison)
        reviewed = self.gate.review(state, reviewer="reviewer", accepted=True)
        with self.assertRaises(RuntimeError):
            self.gate.review(reviewed, reviewer="other", accepted=True)


if __name__ == "__main__":
    unittest.main()
