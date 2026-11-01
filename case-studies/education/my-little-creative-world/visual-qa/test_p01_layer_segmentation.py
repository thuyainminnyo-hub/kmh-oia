import unittest
import numpy as np
from p01_layer_segmentation import segment_masks


class P01LayerSegmentationTests(unittest.TestCase):
    def test_three_masks_returned_and_match_canvas(self):
        rgba=np.zeros((80,60,4),dtype=np.uint8)
        rgba[8:30,5:35]=[240,170,45,255]
        rgba[30:75,5:25]=[150,20,35,255]
        rgba[15:65,30:50]=[230,190,130,255]
        masks=segment_masks(rgba)
        self.assertEqual(set(masks),{"gold_blouse","ruby_longyi","cream_gold_drape"})
        for mask in masks.values():
            self.assertEqual(mask.shape,(80,60))
            self.assertEqual(mask.dtype,np.bool_)

    def test_empty_alpha_returns_empty_masks(self):
        masks=segment_masks(np.zeros((30,30,4),dtype=np.uint8))
        self.assertTrue(all(not mask.any() for mask in masks.values()))

    def test_source_input_must_be_rgba(self):
        with self.assertRaises(ValueError):
            segment_masks(np.zeros((20,20,3),dtype=np.uint8))


if __name__ == "__main__":
    unittest.main()
