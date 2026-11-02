import unittest
import numpy as np
from p01_semantic_layers import make_masks

class SemanticLayerTests(unittest.TestCase):
    def setUp(self):
        self.rgba=np.zeros((1148,617,4),dtype=np.uint8)
        self.rgba[:,:,:3]=[200,120,60]
        self.rgba[:,:,3]=255
    def test_three_boolean_masks(self):
        masks=make_masks(self.rgba)
        self.assertEqual(set(masks),{"Gold_Blouse","Ruby_Longyi","Cream_Gold_Drape"})
        for m in masks.values():
            self.assertEqual(m.shape,(1148,617))
            self.assertEqual(m.dtype,np.bool_)
    def test_visible_region_masks_nonoverlap(self):
        masks=make_masks(self.rgba); names=list(masks)
        for i in range(len(names)):
            for j in range(i+1,len(names)):
                self.assertFalse(np.any(masks[names[i]] & masks[names[j]]))
    def test_wrong_dimensions_rejected(self):
        with self.assertRaises(ValueError):
            make_masks(np.zeros((100,100,4),dtype=np.uint8))
    def test_empty_alpha_is_empty(self):
        self.rgba[:,:,3]=0
        self.assertTrue(all(not x.any() for x in make_masks(self.rgba).values()))

if __name__=="__main__": unittest.main()
