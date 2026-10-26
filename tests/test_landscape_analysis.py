import json
import unittest
from pathlib import Path

from src.landscape_analysis import REQUIRED_ANALYSIS_CATEGORIES, analyze_site
from src.landscape_registry import ObservationCategory, QAStatus


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "landscape_site_valid.json"


def complete_observations(site_id="SITE-DEMO-001"):
    values = {
        "topography": (3.5, "%"),
        "sun": (6.0, "h/day"),
        "drainage": (10.0, "mm/h"),
        "climate": (22.0, "C"),
        "vegetation": (3, "count"),
        "access": (5.0, "m"),
        "utilities": ("available", "category"),
        "hazard": ("not-assessed", "category"),
    }
    return [
        {
            "observation_id": f"OBS-{category.upper()}",
            "site_id": site_id,
            "category": category,
            "value": value,
            "unit": unit,
            "observed_at": "2026-10-20",
            "source_ref": f"synthetic://{site_id}/{category}",
            "method": "synthetic-test-fixture",
            "confidence": 0.9,
            "limitations": "Synthetic test data only; not a real site assessment.",
        }
        for category, (value, unit) in values.items()
    ]


class LandscapeSiteAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_valid_complete_synthetic_evidence_passes_coverage_gate(self):
        report = analyze_site(self.fixture["site"], complete_observations())
        self.assertEqual(report.status, QAStatus.PASS)
        self.assertTrue(report.is_complete)
        self.assertEqual(set(report.observed_categories), set(REQUIRED_ANALYSIS_CATEGORIES))
        self.assertEqual(report.missing_categories, ())
        self.assertIn("evidence_coverage_complete", {finding.code for finding in report.findings})

    def test_missing_categories_are_explicit_and_hold(self):
        report = analyze_site(self.fixture["site"], self.fixture["observations"])
        self.assertEqual(report.status, QAStatus.HOLD)
        self.assertIn(ObservationCategory.DRAINAGE, report.missing_categories)
        self.assertIn("required_evidence_missing", {finding.code for finding in report.findings})

    def test_observation_from_another_site_is_not_used(self):
        observations = complete_observations()
        observations[0] = dict(observations[0], site_id="SITE-OTHER")
        report = analyze_site(self.fixture["site"], observations)
        self.assertEqual(report.status, QAStatus.HOLD)
        self.assertIn("observation_site_mismatch", {issue.code for issue in report.validation_issues})
        self.assertNotIn(ObservationCategory.TOPOGRAPHY, report.observed_categories)

    def test_invalid_observation_is_excluded_and_holds(self):
        observations = complete_observations()
        observations[0] = dict(observations[0], source_ref="")
        report = analyze_site(self.fixture["site"], observations)
        self.assertEqual(report.status, QAStatus.HOLD)
        self.assertIn("observation_registry_invalid", {finding.code for finding in report.findings})

    def test_low_confidence_evidence_is_flagged_with_source_reference(self):
        observations = complete_observations()
        observations[0] = dict(observations[0], confidence=0.4)
        report = analyze_site(self.fixture["site"], observations)
        finding = next(f for f in report.findings if f.code == "low_confidence_evidence")
        self.assertEqual(finding.severity, "warning")
        self.assertEqual(finding.evidence_refs, ("synthetic://SITE-DEMO-001/topography",))

    def test_report_preserves_provenance_and_limitations(self):
        report = analyze_site(self.fixture["site"], complete_observations())
        summary = next(s for s in report.category_summaries if s.category is ObservationCategory.SUN)
        self.assertEqual(summary.evidence_refs, ("synthetic://SITE-DEMO-001/sun",))
        self.assertTrue(summary.limitations)

    def test_invalid_site_payload_returns_hold_not_exception(self):
        report = analyze_site(None, complete_observations())
        self.assertEqual(report.status, QAStatus.HOLD)
        self.assertIn("invalid_site_payload", {issue.code for issue in report.validation_issues})

    def test_malformed_source_refs_do_not_crash_analysis(self):
        site = dict(self.fixture["site"], source_refs=42)
        report = analyze_site(site, complete_observations())
        self.assertEqual(report.status, QAStatus.HOLD)
        self.assertIn("site_registry_invalid", {finding.code for finding in report.findings})

    def test_non_mapping_observation_is_reported(self):
        observations = complete_observations()
        observations[0] = None
        report = analyze_site(self.fixture["site"], observations)
        self.assertEqual(report.status, QAStatus.HOLD)
        self.assertIn("invalid_observation_payload", {issue.code for issue in report.validation_issues})

    def test_report_does_not_claim_design_approval(self):
        report = analyze_site(self.fixture["site"], complete_observations())
        messages = " ".join(f.message.lower() for f in report.findings)
        self.assertIn("not design approval", messages)


if __name__ == "__main__":
    unittest.main()
