import unittest
import numpy as np
from run48_refine import classify_residual_components

class Run48ComponentRefinementTests(unittest.TestCase):
    def empty_masks(self):
        return {"Gold_Blouse": np.zeros((1148,617),bool),
                "Ruby_Longyi": np.zeros((1148,617),bool),
                "Cream_Gold_Drape": np.zeros((1148,617),bool)}

    def rgba(self):
        a=np.zeros((1148,617,4),dtype=np.uint8)
        a[:,:,:3]=[180,120,60]
        return a

    def test_left_shoulder_residual_is_assigned_to_blouse(self):
        a=self.rgba(); a[50:80,70:100,3]=255
        out,decisions,residual,fg=classify_residual_components(a,self.empty_masks())
        self.assertEqual(int(out["Gold_Blouse"].sum()),900)
        self.assertEqual(int(out["Ruby_Longyi"].sum()),0)
        self.assertEqual(int(out["Cream_Gold_Drape"].sum()),0)

    def test_top_right_tab_is_excluded(self):
        a=self.rgba(); a[0:60,380:480,3]=255
        out,decisions,residual,fg=classify_residual_components(a,self.empty_masks())
        self.assertGreater(int(out["Gold_Blouse"].sum()),0)
        self.assertEqual(int(out["Ruby_Longyi"].sum()),0)
        self.assertEqual(int(out["Cream_Gold_Drape"].sum()),0)
        self.assertTrue(any(x["method"]=="split_top_right_paper_tab_from_blouse_shoulder_edge" for x in decisions))

    def test_outer_sleeve_to_drape_component_is_split_at_transition(self):
        a=self.rgba(); a[250:750,520:580,3]=255
        out,decisions,residual,fg=classify_residual_components(a,self.empty_masks())
        self.assertEqual(int(out["Gold_Blouse"].sum()),255*60)
        self.assertEqual(int(out["Cream_Gold_Drape"].sum()),245*60)
        self.assertEqual(int(out["Ruby_Longyi"].sum()),0)

    def test_dimensions_are_validated(self):
        a=self.rgba()
        bad={k:np.zeros((20,20),bool) for k in self.empty_masks()}
        with self.assertRaises(ValueError): classify_residual_components(a,bad)

    def test_unclassified_tiny_component_is_not_guessed(self):
        a=self.rgba(); a[700:708,300:308,3]=255
        out,decisions,residual,fg=classify_residual_components(a,self.empty_masks())
        self.assertEqual(int(np.logical_or.reduce(list(out.values())).sum()),0)
        self.assertEqual(int(residual.sum()),64)

if __name__ == "__main__":
    unittest.main(verbosity=2)