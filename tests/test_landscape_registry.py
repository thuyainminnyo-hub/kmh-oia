import json
import unittest
from pathlib import Path

from src.landscape_registry import (
    ObservationCategory,
    QAStatus,
    SiteRecord,
    validate_observation_payload,
    validate_site_payload,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "landscape_site_valid.json"


class LandscapeRegistryValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_synthetic_site_fixture_passes_validation(self):
        report = validate_site_payload(self.fixture["site"])
        self.assertTrue(report.is_valid, report.issues)
        self.assertFalse(report.requires_hold)

    def test_synthetic_observation_fixtures_pass_validation(self):
        for observation in self.fixture["observations"]:
            with self.subTest(observation=observation["observation_id"]):
                report = validate_observation_payload(observation)
                self.assertTrue(report.is_valid, report.issues)

    def test_typed_models_are_explicit_and_frozen(self):
        site = SiteRecord(
            site_id="SITE-1",
            boundary_ref="synthetic://boundary",
            area_value=100.0,
            area_unit="m2",
            jurisdiction="TEST",
            source_refs=("synthetic://source",),
        )
        self.assertEqual(site.site_id, "SITE-1")
        self.assertEqual(ObservationCategory.TOPOGRAPHY.value, "topography")
        self.assertEqual(QAStatus.HOLD.value, "HOLD")
        with self.assertRaises((AttributeError, TypeError)):
            site.area_value = 200.0

    def test_missing_required_site_fields_are_reported(self):
        report = validate_site_payload({})
        missing_paths = {issue.path for issue in report.issues}
        self.assertFalse(report.is_valid)
        self.assertTrue(report.requires_hold)
        self.assertTrue(
            {"site_id", "boundary_ref", "area_value", "area_unit",
             "jurisdiction", "source_refs"}.issubset(missing_paths)
        )

    def test_blank_boundary_is_rejected(self):
        payload = dict(self.fixture["site"], boundary_ref="   ")
        report = validate_site_payload(payload)
        self.assertIn("required_field_blank", {issue.code for issue in report.issues})

    def test_non_positive_area_is_rejected(self):
        for area in (0, -1, float("inf"), float("nan"), True, "12"):
            with self.subTest(area=area):
                payload = dict(self.fixture["site"], area_value=area)
                report = validate_site_payload(payload)
                self.assertIn("invalid_numeric_value", {issue.code for issue in report.issues})

    def test_unsupported_area_unit_is_rejected(self):
        payload = dict(self.fixture["site"], area_unit="square bananas")
        report = validate_site_payload(payload)
        self.assertIn("unsupported_unit", {issue.code for issue in report.issues})

    def test_site_requires_source_provenance(self):
        for refs in ([], [""], None):
            with self.subTest(refs=refs):
                payload = dict(self.fixture["site"], source_refs=refs)
                report = validate_site_payload(payload)
                self.assertTrue(
                    {issue.code for issue in report.issues}
                    & {"provenance_missing", "provenance_invalid", "required_field_missing"}
                )

    def test_missing_observation_source_is_rejected(self):
        payload = dict(self.fixture["observations"][0], source_ref="")
        report = validate_observation_payload(payload)
        self.assertIn("provenance_missing", {issue.code for issue in report.issues})

    def test_unsupported_observation_unit_is_rejected(self):
        payload = dict(self.fixture["observations"][0], unit="unknown-unit")
        report = validate_observation_payload(payload)
        self.assertIn("unsupported_unit", {issue.code for issue in report.issues})

    def test_invalid_observation_date_is_rejected(self):
        payload = dict(self.fixture["observations"][0], observed_at="last Tuesday")
        report = validate_observation_payload(payload)
        self.assertIn("invalid_observed_at", {issue.code for issue in report.issues})

    def test_confidence_must_be_finite_and_between_zero_and_one(self):
        for confidence in (-0.1, 1.1, float("inf"), float("nan"), True, "high"):
            with self.subTest(confidence=confidence):
                payload = dict(self.fixture["observations"][0], confidence=confidence)
                report = validate_observation_payload(payload)
                self.assertIn("invalid_confidence", {issue.code for issue in report.issues})

    def test_unknown_observation_category_is_rejected(self):
        payload = dict(self.fixture["observations"][0], category="fortune-telling")
        report = validate_observation_payload(payload)
        self.assertIn("invalid_category", {issue.code for issue in report.issues})

    def test_missing_observation_fields_are_reported(self):
        report = validate_observation_payload({})
        missing_paths = {issue.path for issue in report.issues}
        self.assertFalse(report.is_valid)
        self.assertTrue(
            {"observation_id", "site_id", "category", "value", "unit",
             "observed_at", "source_ref", "method", "confidence"}.issubset(missing_paths)
        )

    def test_boolean_is_not_accepted_as_numeric_observation(self):
        payload = dict(self.fixture["observations"][0], value=True)
        report = validate_observation_payload(payload)
        self.assertIn("invalid_value_type", {issue.code for issue in report.issues})


if __name__ == "__main__":
    unittest.main()
