import unittest

from src.production_runbook import ProductionRunbookActivator


class ProductionRunbookActivatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.activator = ProductionRunbookActivator()
        self.sections = ProductionRunbookActivator.REQUIRED_SECTIONS

    def test_prepare_requires_runbook_id(self) -> None:
        with self.assertRaises(ValueError):
            self.activator.prepare(runbook_id=" ", sections=self.sections)

    def test_activation_blocks_missing_required_sections(self) -> None:
        state = self.activator.prepare(
            runbook_id="stage14-v1",
            sections=tuple(section for section in self.sections if section != "rollback"),
        )
        blocked = self.activator.activate(state)
        self.assertEqual(blocked.phase, "blocked")
        self.assertFalse(blocked.activated)
        self.assertIn("rollback", blocked.reason)

    def test_activation_requires_ready_state(self) -> None:
        state = self.activator.prepare(runbook_id="stage14-v1", sections=self.sections)
        activated = self.activator.activate(state)
        with self.assertRaises(RuntimeError):
            self.activator.activate(activated)

    def test_complete_runbook_activates(self) -> None:
        state = self.activator.prepare(runbook_id="stage14-v1", sections=self.sections)
        activated = self.activator.activate(state)
        self.assertTrue(activated.activated)
        self.assertEqual(activated.phase, "activated")
        self.assertEqual(activated.reason, "runbook readiness validated")
        self.activator.validate(activated)

    def test_validation_requires_activation(self) -> None:
        state = self.activator.prepare(runbook_id="stage14-v1", sections=self.sections)
        with self.assertRaises(RuntimeError):
            self.activator.validate(state)


if __name__ == "__main__":
    unittest.main()
