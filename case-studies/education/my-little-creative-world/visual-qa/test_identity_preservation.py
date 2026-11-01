import tempfile
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
from identity_preservation import evaluate_identity_preservation


class IdentityPreservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.original = np.zeros((8, 8, 3), dtype=np.uint8)
        self.original[2:6, 2:6] = [120, 80, 40]
        self.output = self.original.copy()
        self.mask = np.zeros((8, 8), dtype=np.uint8)
        self.mask[2:6, 2:6] = 255
        self.mask[1, 1] = 128
        self.save()

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        Image.fromarray(self.original).save(self.root / "original.png")
        Image.fromarray(self.output).save(self.root / "output.png")
        Image.fromarray(self.mask).save(self.root / "mask.png")

    def evaluate(self):
        return evaluate_identity_preservation(
            self.root / "original.png", self.root / "output.png", self.root / "mask.png"
        )

    def test_identical_protected_core_passes(self):
        result = self.evaluate()
        self.assertTrue(result["pass"])
        self.assertEqual(result["opaque_core_exact_match_ratio"], 1.0)
        self.assertEqual(result["changed_rgb_pixels_in_opaque_core"], 0)

    def test_changed_protected_pixel_fails(self):
        self.output[3, 3] = [255, 0, 0]
        self.save()
        result = self.evaluate()
        self.assertFalse(result["pass"])
        self.assertEqual(result["changed_rgb_pixels_in_opaque_core"], 1)

    def test_mask_dimension_mismatch_fails_closed(self):
        Image.fromarray(np.zeros((7, 7), dtype=np.uint8)).save(self.root / "mask.png")
        with self.assertRaises(ValueError):
            self.evaluate()

    def test_empty_mask_fails_closed(self):
        self.mask[:] = 0
        self.save()
        with self.assertRaises(ValueError):
            self.evaluate()


if __name__ == "__main__":
    unittest.main()
