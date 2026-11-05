import unittest
import numpy as np
from p01_master_sheet_extract import fill_small_internal_holes, build_rgba, make_candidate_mask

class ExtractionTests(unittest.TestCase):
    def test_small_internal_holes_are_filled(self):
        m=np.ones((20,20),np.uint8); m[8:10,8:10]=0
        self.assertEqual(int(fill_small_internal_holes(m,10).sum()),400)
    def test_large_hole_is_preserved(self):
        m=np.ones((40,40),np.uint8); m[10:25,10:25]=0
        self.assertEqual(int(fill_small_internal_holes(m,90)[15:20,15:20].sum()),0)
    def test_rgba_shape_and_bbox(self):
        rgb=np.full((30,40,3),255,np.uint8); mask=np.zeros((30,40),np.uint8); mask[5:25,7:31]=1
        rgba,bbox=build_rgba(rgb,mask)
        self.assertEqual(rgba.shape,(20,24,4)); self.assertEqual(bbox,[7,5,31,25])
    def test_non_rgb_input_rejected(self):
        with self.assertRaises(ValueError): make_candidate_mask(np.zeros((20,20),np.uint8))

if __name__=="__main__": unittest.main()
