import math
import unittest

from src.visual_continuity import (
    ContinuityPolicy, ContinuityStatus, RuleBasedContinuityEvaluator, ShotEvidence,
)


def evidence(scores, **overrides):
    values = dict(
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
    values.update(overrides)
    return ShotEvidence(**values)


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

    def test_invalid_score_above_range_rejected(self):
        with self.assertRaises(ValueError):
            evidence(dict(self.complete_scores, props=1.2))

    def test_boolean_and_non_finite_scores_rejected(self):
        for score in (True, float("nan"), float("inf"), float("-inf")):
            with self.subTest(score=score):
                with self.assertRaises(ValueError):
                    evidence(dict(self.complete_scores, props=score))

    def test_missing_reference_rejected(self):
        with self.assertRaises(ValueError):
            evidence(self.complete_scores, reference_asset_ids=())

    def test_blank_or_duplicate_reference_ids_rejected(self):
        for ids in (("CHAR", " "), ("CHAR", "CHAR")):
            with self.subTest(ids=ids):
                with self.assertRaises(ValueError):
                    evidence(self.complete_scores, reference_asset_ids=ids)

    def test_empty_or_blank_evidence_uris_rejected(self):
        for uris in ((), (" ",)):
            with self.subTest(uris=uris):
                with self.assertRaises(ValueError):
                    evidence(self.complete_scores, evidence_uris=uris)

    def test_policy_rejects_missing_required_threshold(self):
        with self.assertRaises(ValueError):
            ContinuityPolicy(thresholds={"face_identity": 0.9},
                             required_dimensions=("face_identity", "costume"))

    def test_policy_rejects_boolean_and_non_finite_thresholds(self):
        for threshold in (True, float("nan"), float("inf")):
            with self.subTest(threshold=threshold):
                with self.assertRaises(ValueError):
                    ContinuityPolicy(thresholds={"face_identity": threshold},
                                     required_dimensions=("face_identity",))

    def test_policy_rejects_duplicate_required_dimensions(self):
        with self.assertRaises(ValueError):
            ContinuityPolicy(required_dimensions=("face_identity", "face_identity"))

    def test_input_mappings_are_defensively_copied_and_read_only(self):
        scores = dict(self.complete_scores)
        item = evidence(scores)
        scores["face_identity"] = 0.0
        self.assertEqual(item.scores["face_identity"], 0.98)
        with self.assertRaises(TypeError):
            item.scores["face_identity"] = 0.0

        thresholds = {"face_identity": 0.9}
        policy = ContinuityPolicy(thresholds=thresholds,
                                  required_dimensions=("face_identity",))
        thresholds["face_identity"] = 0.1
        self.assertEqual(policy.thresholds["face_identity"], 0.9)
        with self.assertRaises(TypeError):
            policy.thresholds["face_identity"] = 0.1

    def test_unknown_score_dimension_rejected(self):
        with self.assertRaises(ValueError):
            self.evaluator.evaluate(evidence(dict(self.complete_scores, mystery=0.99)))

    def test_report_is_serializable(self):
        report = self.evaluator.evaluate(evidence(self.complete_scores))
        payload = report.to_dict()
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["policy_version"], "vcie-policy-v1")
        self.assertTrue(payload["report_id"].startswith("vcie-"))


if __name__ == "__main__":
    unittest.main()
