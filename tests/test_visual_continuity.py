import unittest

from src.visual_continuity import (
    ContinuityPolicy, ContinuityStatus, RuleBasedContinuityEvaluator, ShotEvidence,
)


def evidence(scores):
    return ShotEvidence(
        film_id="FILM-001",
        scene_id="SCENE-001",
        shot_id="SHOT-001",
        reference_asset_ids=("CHAR-REF-001", "LOC-REF-001"),
        generated_asset_id="ASSET-GEN-001",
        evaluator="fixture-evaluator",
        evaluator_version="0.1",
        scores=scores,
        evidence_uris=("evidence://run/001",),
    )


class TestVisualContinuity(unittest.TestCase):
    def setUp(self):
        self.evaluator = RuleBasedContinuityEvaluator()
        self.complete_scores = {
            "face_identity": 0.98,
            "costume": 0.95,
            "props": 0.93,
            "environment": 0.94,
            "lighting": 0.90,
        }

    def test_all_dimensions_above_threshold_pass(self):
        report = self.evaluator.evaluate(evidence(self.complete_scores))
        self.assertEqual(report.status, ContinuityStatus.PASS)
        self.assertEqual(report.missing_dimensions, ())
        self.assertEqual(report.failed_dimensions, ())

    def test_low_face_identity_requires_rework(self):
        scores = dict(self.complete_scores, face_identity=0.70)
        report = self.evaluator.evaluate(evidence(scores))
        self.assertEqual(report.status, ContinuityStatus.REWORK)
        self.assertEqual(report.failed_dimensions, ("face_identity",))
        self.assertTrue(report.human_review_required)

    def test_missing_dimension_never_passes(self):
        scores = dict(self.complete_scores)
        del scores["costume"]
        report = self.evaluator.evaluate(evidence(scores))
        self.assertEqual(report.status, ContinuityStatus.REVIEW)
        self.assertEqual(report.missing_dimensions, ("costume",))

    def test_invalid_score_rejected(self):
        with self.assertRaises(ValueError):
            evidence(dict(self.complete_scores, props=1.2))

    def test_missing_reference_rejected(self):
        with self.assertRaises(ValueError):
            ShotEvidence("F", "S", "SH", (), "A", "eval", "1", self.complete_scores)

    def test_policy_rejects_missing_required_threshold(self):
        with self.assertRaises(ValueError):
            ContinuityPolicy(thresholds={"face_identity": 0.9},
                             required_dimensions=("face_identity", "costume"))

    def test_report_is_serializable(self):
        report = self.evaluator.evaluate(evidence(self.complete_scores))
        payload = report.to_dict()
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["policy_version"], "vcie-policy-v1")
        self.assertTrue(payload["report_id"].startswith("vcie-"))


if __name__ == "__main__":
    unittest.main()
