import unittest

from src.post_deployment_review import PostDeploymentReviewController


class PostDeploymentReviewControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = PostDeploymentReviewController()
        self.evidence = {key: f"{key}-evidence" for key in self.controller.REQUIRED_EVIDENCE}

    def test_start_requires_deployment_id(self) -> None:
        with self.assertRaises(ValueError):
            self.controller.start(deployment_id=" ")

    def test_review_blocks_missing_production_evidence(self) -> None:
        state = self.controller.start(deployment_id="deploy-14")
        evidence = dict(self.evidence)
        del evidence["telemetry"]
        blocked = self.controller.review(state, evidence=evidence)
        self.assertEqual(blocked.phase, "blocked")
        self.assertFalse(blocked.validated)
        self.assertIn("telemetry", blocked.reason)

    def test_complete_evidence_validates_review(self) -> None:
        state = self.controller.start(deployment_id="deploy-14")
        reviewed = self.controller.review(state, evidence=self.evidence, findings=("latency observation recorded",))
        self.assertEqual(reviewed.phase, "reviewed")
        self.assertTrue(reviewed.validated)
        self.assertEqual(reviewed.findings, ("latency observation recorded",))
        self.controller.validate(reviewed)

    def test_review_requires_started_state(self) -> None:
        state = self.controller.start(deployment_id="deploy-14")
        reviewed = self.controller.review(state, evidence=self.evidence)
        with self.assertRaises(RuntimeError):
            self.controller.review(reviewed, evidence=self.evidence)

    def test_validation_cannot_bypass_incomplete_review(self) -> None:
        state = self.controller.start(deployment_id="deploy-14")
        with self.assertRaises(RuntimeError):
            self.controller.validate(state)


if __name__ == "__main__":
    unittest.main()
