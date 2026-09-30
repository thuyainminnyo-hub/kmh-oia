import unittest

from scripts.performance_load_validation import measure


class Stage13PerformanceLoadTests(unittest.TestCase):
    def test_bounded_concurrent_runtime_completes(self):
        result = measure(iterations=8, workers=2)
        self.assertEqual(result["iterations"], 8)
        self.assertEqual(result["workers"], 2)
        self.assertEqual(result["completed"], 8)
        self.assertGreaterEqual(result["wall_ms"], 0)
        self.assertGreaterEqual(result["max_ms"], result["min_ms"])

    def test_invalid_load_parameters_are_rejected(self):
        with self.assertRaises(ValueError):
            measure(iterations=0)
        with self.assertRaises(ValueError):
            measure(workers=0)


if __name__ == "__main__":
    unittest.main()
