"""Static safety/contract checks for the offline body-map UI prototype."""
import unittest
from pathlib import Path

UI_PATH = Path(__file__).resolve().parents[1] / "pilots" / "kmh_medicore_bodymap" / "ui" / "body-map-pilot.html"


class BodyMapUiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = UI_PATH.read_text(encoding="utf-8")

    def test_ui_declares_local_synthetic_nonclinical_boundary(self):
        self.assertIn("LOCAL SYNTHETIC DEMO", self.html)
        self.assertIn("NOT FOR CLINICAL USE", self.html)
        self.assertIn("does not send, store, or persist patient data", self.html)

    def test_requested_default_scenario_is_present(self):
        self.assertIn('data-view="front" aria-pressed="true"', self.html)
        self.assertIn('data-region="SKULL"', self.html)
        self.assertIn('value="fracture"', self.html)
        self.assertIn('value="cast_or_splint"', self.html)
        self.assertIn('status:"proposed"', self.html)
        self.assertIn('status:"draft"', self.html)

    def test_region_controls_and_keyboard_interaction_exist(self):
        for region in ("SKULL", "SPINE", "PELVIS", "UPPER_LIMB", "LOWER_LIMB"):
            with self.subTest(region=region):
                self.assertIn(f'data-region="{region}"', self.html)
                self.assertIn(f'data-region-button="{region}"', self.html)
        self.assertIn('e.key==="Enter"||e.key===" "', self.html)

    def test_ui_has_no_network_or_persistent_browser_storage_calls(self):
        for forbidden in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "<script src=", "<link rel="):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.html)

    def test_ui_preview_does_not_claim_to_save(self):
        self.assertIn("Draft only — nothing has been saved.", self.html)
        self.assertIn("nothing was saved", self.html)


if __name__ == "__main__":
    unittest.main()
