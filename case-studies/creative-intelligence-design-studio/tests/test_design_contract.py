import copy
import json
import unittest
from pathlib import Path

from scripts.validate_design_contract import contrast_ratio, validate_contract

CONTRACT_PATH = Path(__file__).resolve().parents[1] / "contracts" / "design-contract.json"


class DesignContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_baseline_contract_passes(self):
        self.assertEqual(validate_contract(self.contract), [])

    def test_low_contrast_pair_fails(self):
        candidate = copy.deepcopy(self.contract)
        candidate["tokens"]["color"]["text_primary"] = "#777777"
        errors = validate_contract(candidate)
        self.assertTrue(any("contrast text_primary/canvas" in item for item in errors))

    def test_missing_required_color_fails(self):
        candidate = copy.deepcopy(self.contract)
        del candidate["tokens"]["color"]["focus"]
        errors = validate_contract(candidate)
        self.assertTrue(any("missing color tokens" in item for item in errors))

    def test_reduced_motion_must_be_preserved(self):
        candidate = copy.deepcopy(self.contract)
        candidate["accessibility"]["respect_reduced_motion"] = False
        errors = validate_contract(candidate)
        self.assertIn("respect_reduced_motion must be true", errors)

    def test_unknown_token_reference_fails(self):
        candidate = copy.deepcopy(self.contract)
        candidate["required_contrast_pairs"][0]["foreground"] = "not_a_token"
        errors = validate_contract(candidate)
        self.assertTrue(any("unknown token" in item for item in errors))

    def test_contrast_ratio_white_on_brand(self):
        ratio = contrast_ratio("#FFFFFF", self.contract["tokens"]["color"]["brand_primary"])
        self.assertGreaterEqual(ratio, 4.5)


if __name__ == "__main__":
    unittest.main()
