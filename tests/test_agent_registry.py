import unittest

from src.agent_registry import AgentRecord, AgentRegistry, AgentStatus


def record(agent_id="kmh.planner", **overrides):
    values = {
        "agent_id": agent_id,
        "name": "KMH Planner",
        "role": "planning",
        "owner": "KMH",
        "version": "1.0.0",
        "capabilities": ("task.plan", "task.read"),
    }
    values.update(overrides)
    return AgentRecord(**values)


class AgentRegistryTests(unittest.TestCase):
    def test_register_and_get(self):
        registry = AgentRegistry()
        expected = record()
        self.assertEqual(registry.register(expected), expected)
        self.assertEqual(registry.get("kmh.planner"), expected)

    def test_duplicate_identity_is_rejected(self):
        registry = AgentRegistry()
        registry.register(record())
        with self.assertRaisesRegex(ValueError, "already registered"):
            registry.register(record())

    def test_invalid_identity_and_missing_metadata_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "stable lowercase"):
            record(agent_id="KMH Planner")
        with self.assertRaisesRegex(ValueError, "owner is required"):
            record(owner=" ")
        with self.assertRaisesRegex(ValueError, "at least one capability"):
            record(capabilities=())

    def test_capabilities_are_normalized_and_unique(self):
        normalized = record(capabilities=(" task.read ", "task.plan"))
        self.assertEqual(normalized.capabilities, ("task.read", "task.plan"))
        with self.assertRaisesRegex(ValueError, "must be unique"):
            record(capabilities=("task.read", " task.read "))

    def test_lifecycle_suspend_and_reactivate(self):
        registry = AgentRegistry()
        registry.register(record())
        suspended = registry.transition_status(
            "kmh.planner", AgentStatus.SUSPENDED
        )
        self.assertEqual(suspended.status, AgentStatus.SUSPENDED)
        active = registry.transition_status("kmh.planner", AgentStatus.ACTIVE)
        self.assertEqual(active.status, AgentStatus.ACTIVE)

    def test_revoked_agent_cannot_be_reactivated(self):
        registry = AgentRegistry()
        registry.register(record())
        registry.transition_status("kmh.planner", AgentStatus.REVOKED)
        with self.assertRaisesRegex(ValueError, "invalid agent lifecycle"):
            registry.transition_status("kmh.planner", AgentStatus.ACTIVE)

    def test_status_filter_and_stable_order(self):
        registry = AgentRegistry()
        registry.register(record("kmh.writer", name="Writer"))
        registry.register(record("kmh.planner", name="Planner"))
        registry.transition_status("kmh.writer", AgentStatus.SUSPENDED)
        self.assertEqual(
            [item.agent_id for item in registry.list()],
            ["kmh.planner", "kmh.writer"],
        )
        self.assertEqual(
            [item.agent_id for item in registry.list(AgentStatus.ACTIVE)],
            ["kmh.planner"],
        )


if __name__ == "__main__":
    unittest.main()
