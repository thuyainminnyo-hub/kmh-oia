import unittest

from src.controlled_promotion import ControlledProductionPromotion


class ControlledProductionPromotionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = ControlledProductionPromotion()

    def test_start_requires_release_id(self) -> None:
        with self.assertRaises(ValueError):
            self.controller.start(release_id=" ")

    def test_promotion_requires_health_gate(self) -> None:
        state = self.controller.start(release_id="rc-14")
        blocked = self.controller.promote(state, health_passed=False)
        self.assertEqual(blocked.phase, "blocked")
        self.assertFalse(blocked.promoted)
        self.assertEqual(blocked.reason, "health gate failed")

    def test_successful_health_gated_promotion(self) -> None:
        state = self.controller.start(release_id="rc-14")
        promoted = self.controller.promote(state, health_passed=True)
        self.assertEqual(promoted.phase, "promoted")
        self.assertTrue(promoted.promoted)
        self.assertEqual(promoted.reason, "health gate passed")

    def test_validation_requires_promoted_state(self) -> None:
        state = self.controller.start(release_id="rc-14")
        with self.assertRaises(RuntimeError):
            self.controller.validate(state)

        promoted = self.controller.promote(state, health_passed=True)
        self.controller.validate(promoted)

    def test_blocked_promotion_cannot_be_repromoted(self) -> None:
        state = self.controller.start(release_id="rc-14")
        blocked = self.controller.promote(state, health_passed=False)
        with self.assertRaises(RuntimeError):
            self.controller.promote(blocked, health_passed=True)


if __name__ == "__main__":
    unittest.main()
