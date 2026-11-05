import unittest
import numpy as np
from neck_seam_refinement import refine_neck_mask


class NeckSeamRefinementTests(unittest.TestCase):
    def setUp(self):
        self.mask = np.zeros((500, 700), dtype=np.uint8)
        self.mask[100:420, 300:700] = 255

    def test_upper_head_region_is_unchanged(self):
        refined = refine_neck_mask(self.mask)
        np.testing.assert_array_equal(refined[:378], self.mask[:378])

    def test_lower_central_neck_is_tapered(self):
        refined = refine_neck_mask(self.mask)
        self.assertLess(int(refined[410, 500]), int(self.mask[410, 500]))
        self.assertEqual(int(refined[420, 500]), 0)

    def test_side_strands_zone_is_not_tapered_at_same_row(self):
        refined = refine_neck_mask(self.mask)
        self.assertEqual(int(refined[400, 390]), int(self.mask[400, 390]))
        self.assertEqual(int(refined[400, 630]), int(self.mask[400, 630]))

    def test_invalid_mask_and_coordinates_fail_closed(self):
        with self.assertRaises(ValueError):
            refine_neck_mask(np.zeros((10, 10, 3), dtype=np.uint8))
        with self.assertRaises(ValueError):
            refine_neck_mask(self.mask, y_start=420, y_end=400)


if __name__ == "__main__":
    unittest.main()
