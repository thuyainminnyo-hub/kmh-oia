import unittest
import numpy as np
from benchmark_metrics import score_masks


class SegmentationMetricTests(unittest.TestCase):
    def test_identical_masks_score_one(self):
        mask = np.zeros((12, 12), dtype=bool)
        mask[3:9, 4:8] = True
        result = score_masks(mask, mask, tolerance=1)
        self.assertEqual(result["iou"], 1.0)
        self.assertEqual(result["boundary_f_score"], 1.0)

    def test_disjoint_masks_score_zero_iou(self):
        a = np.zeros((12, 12), dtype=bool)
        b = np.zeros((12, 12), dtype=bool)
        a[1:4, 1:4] = True
        b[8:11, 8:11] = True
        result = score_masks(a, b, tolerance=0)
        self.assertEqual(result["iou"], 0.0)

    def test_dimension_mismatch_fails_closed(self):
        with self.assertRaises(ValueError):
            score_masks(np.zeros((4, 4)), np.zeros((5, 5)))

    def test_empty_masks_are_well_defined(self):
        empty = np.zeros((8, 8), dtype=bool)
        result = score_masks(empty, empty)
        self.assertEqual(result["iou"], 1.0)
        self.assertEqual(result["boundary_f_score"], 1.0)


if __name__ == "__main__":
    unittest.main()
