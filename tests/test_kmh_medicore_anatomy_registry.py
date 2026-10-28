"""Contract checks for the local illustrative anatomy registry."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "pilots" / "kmh_medicore_bodymap" / "anatomy_registry.v0.2.json"
SCHEMA_PATH = ROOT / "schemas" / "medicore" / "body-map-annotation-0.1.schema.json"


class AnatomyRegistryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_registry_codes_match_schema_codes(self):
        registry_codes = {item["code"] for item in self.registry["regions"]}
        schema_codes = set(self.schema["properties"]["anatomy_code"]["enum"])
        self.assertEqual(registry_codes, schema_codes)

    def test_registry_codes_and_labels_are_unique(self):
        codes = [item["code"] for item in self.registry["regions"]]
        labels = [item["label"] for item in self.registry["regions"]]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(len(labels), len(set(labels)))

    def test_every_region_has_valid_views_and_laterality(self):
        for region in self.registry["regions"]:
            with self.subTest(region=region["code"]):
                self.assertTrue(region["views"])
                self.assertTrue(set(region["views"]) <= {"front", "back", "both"})
                self.assertTrue(region["laterality"])
                self.assertTrue(
                    set(region["laterality"])
                    <= {"left", "right", "bilateral", "midline", "not_applicable"}
                )

    def test_registry_explicitly_disclaims_clinical_authority(self):
        self.assertIn("not an authoritative clinical terminology", self.registry["authority"])
        self.assertIn("No diagnosis inference", self.registry["explicit_non_goals"])
        self.assertIn("No treatment recommendation", self.registry["explicit_non_goals"])


if __name__ == "__main__":
    unittest.main()
