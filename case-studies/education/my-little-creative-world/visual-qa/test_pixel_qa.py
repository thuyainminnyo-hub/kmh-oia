import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
from pixel_qa import evaluate


class PixelQATests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.original = np.zeros((6, 6, 3), dtype=np.uint8)
        self.output = self.original.copy()
        self.target = np.zeros((6, 6), dtype=np.uint8)
        self.protected = np.zeros((6, 6), dtype=np.uint8)
        self.target[2:4, 2:4] = 255
        self.protected[0:2, 0:2] = 255
        self.output[2:4, 2:4] = 180
        for name, arr in [("original.png", self.original), ("output.png", self.output),
                          ("target.png", self.target), ("protected.png", self.protected)]:
            Image.fromarray(arr).save(self.root / name)

    def tearDown(self):
        self.tmp.cleanup()

    def paths(self):
        return [self.root / name for name in ("original.png", "output.png", "target.png", "protected.png")]

    def test_full_coverage_and_identity_preserved_pass(self):
        result = evaluate(*self.paths())
        self.assertTrue(result["pass"])
        self.assertEqual(result["target_pixels"], 4)
        self.assertEqual(result["uncovered_target_pixels"], 0)
        self.assertEqual(result["protected_changed_pixels"], 0)

    def test_protected_region_change_fails(self):
        self.output[0, 0] = 255
        Image.fromarray(self.output).save(self.root / "output.png")
        self.assertFalse(evaluate(*self.paths())["pass"])

    def test_uncovered_target_pixel_fails(self):
        self.output[2, 2] = 0
        Image.fromarray(self.output).save(self.root / "output.png")
        self.assertFalse(evaluate(*self.paths())["pass"])

    def test_spillover_outside_allowed_masks_fails(self):
        self.output[5, 5] = 255
        Image.fromarray(self.output).save(self.root / "output.png")
        self.assertFalse(evaluate(*self.paths())["pass"])

    def test_dimension_mismatch_fails_closed(self):
        Image.fromarray(np.zeros((5, 5, 3), dtype=np.uint8)).save(self.root / "output.png")
        with self.assertRaises(ValueError):
            evaluate(*self.paths())


if __name__ == "__main__":
    unittest.main()
