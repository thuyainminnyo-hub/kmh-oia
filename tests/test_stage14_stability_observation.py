import unittest

from src.stability_observation import StabilityObservationController


class Stage14StabilityObservationTests(unittest.TestCase):
    def test_all_healthy_samples_are_stable(self):
        result = StabilityObservationController().observe([
            {"health": True, "errors": True, "latency": True},
            {"health": True, "errors": True, "latency": True},
        ])
        self.assertEqual((2, 2, True), (result.samples, result.healthy_samples, result.stable))

    def test_failed_sample_blocks_stability(self):
        result = StabilityObservationController().observe([
            {"health": True, "errors": True},
            {"health": True, "errors": False},
        ])
        self.assertEqual((2, 1, False), (result.samples, result.healthy_samples, result.stable))

    def test_empty_samples_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "requires samples"):
            StabilityObservationController().observe([])

    def test_empty_signal_map_is_not_healthy(self):
        result = StabilityObservationController().observe([{}])
        self.assertEqual((1, 0, False), (result.samples, result.healthy_samples, result.stable))


if __name__ == "__main__":
    unittest.main()
