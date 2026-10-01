"""Tests for Stage 15 stabilization controller."""
import unittest

from src.stabilization import StabilizationController


class StabilizationControllerTests(unittest.TestCase):
    def setUp(self):
        self.controller = StabilizationController()

    def test_requires_explicit_release_and_positive_window_gate(self):
        with self.assertRaises(ValueError):
            self.controller.start(release_id=" ", required_healthy_windows=2)
        with self.assertRaises(ValueError):
            self.controller.start(release_id="r1", required_healthy_windows=0)
        with self.assertRaises(ValueError):
            self.controller.start(release_id="r1", required_healthy_windows=True)

    def test_stabilizes_after_required_healthy_windows(self):
        state = self.controller.start(release_id="r1", required_healthy_windows=2)
        state = self.controller.observe(state, healthy=True)
        self.assertFalse(state.stable)
        state = self.controller.observe(state, healthy=True)
        self.assertTrue(state.stable)
        self.assertEqual(state.healthy_windows, 2)
        self.controller.validate(state)

    def test_unhealthy_window_does_not_count_as_healthy(self):
        state = self.controller.start(release_id="r1", required_healthy_windows=2)
        state = self.controller.observe(state, healthy=False)
        state = self.controller.observe(state, healthy=True)
        self.assertEqual(state.windows_observed, 2)
        self.assertEqual(state.healthy_windows, 1)
        with self.assertRaises(RuntimeError):
            self.controller.validate(state)

    def test_observation_requires_boolean_and_stable_state_is_terminal(self):
        state = self.controller.start(release_id="r1", required_healthy_windows=1)
        with self.assertRaises(ValueError):
            self.controller.observe(state, healthy=1)
        state = self.controller.observe(state, healthy=True)
        with self.assertRaises(RuntimeError):
            self.controller.observe(state, healthy=True)


if __name__ == "__main__":
    unittest.main()
