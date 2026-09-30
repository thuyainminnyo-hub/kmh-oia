import unittest

from src.production_change_control import ProductionChangeController


class ProductionChangeControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = ProductionChangeController()

    def test_submit_requires_change_id(self) -> None:
        with self.assertRaises(ValueError):
            self.controller.submit(change_id=" ")

    def test_rejected_change_cannot_validate(self) -> None:
        state = self.controller.submit(change_id="chg-14")
        rejected = self.controller.approve(state, approved=False)
        self.assertEqual(rejected.phase, "rejected")
        with self.assertRaises(RuntimeError):
            self.controller.validate(rejected, validation_passed=True)

    def test_approval_is_required_before_validation(self) -> None:
        state = self.controller.submit(change_id="chg-14")
        with self.assertRaises(RuntimeError):
            self.controller.validate(state, validation_passed=True)

    def test_failed_validation_blocks_execution(self) -> None:
        state = self.controller.submit(change_id="chg-14")
        approved = self.controller.approve(state, approved=True)
        failed = self.controller.validate(approved, validation_passed=False)
        self.assertEqual(failed.phase, "validation_failed")
        with self.assertRaises(RuntimeError):
            self.controller.require_execution_ready(failed)

    def test_approved_and_validated_change_is_execution_ready(self) -> None:
        state = self.controller.submit(change_id="chg-14")
        approved = self.controller.approve(state, approved=True)
        ready = self.controller.validate(approved, validation_passed=True)
        self.assertEqual(ready.phase, "execution_ready")
        self.assertTrue(ready.approved)
        self.assertTrue(ready.validated)
        self.controller.require_execution_ready(ready)


if __name__ == "__main__":
    unittest.main()
