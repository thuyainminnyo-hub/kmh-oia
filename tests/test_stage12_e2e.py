import unittest

from src.agent import AgentDecision
from src.components import OIARuntime
from src.knowledge import KnowledgeItem, StaticKnowledgeSource
from src.memory import InMemoryMemoryStore


class AuditableAgent:
    def decide(self, request):
        return AgentDecision("echo", request.goal, "stage-12-e2e")


class Stage12E2EValidationTests(unittest.TestCase):
    def _run_goal(self, session_id):
        memory = InMemoryMemoryStore()
        knowledge = StaticKnowledgeSource([
            KnowledgeItem("production-like-source", "bounded validation knowledge"),
        ])
        runtime = OIARuntime(
            memory=memory,
            knowledge=knowledge,
            agent=AuditableAgent(),
        )
        response, stages, events = runtime.execute_detailed(
            "production-like validation goal",
            session_id=session_id,
        )
        return response, stages, events, memory

    def test_pv3_complete_goal_is_repeatable_and_auditable(self):
        first = self._run_goal("pv3-1")
        second = self._run_goal("pv3-2")

        for response, stages, events, memory in (first, second):
            self.assertEqual(response, "production-like validation goal")
            self.assertEqual(
                stages,
                [
                    "input_gateway", "oia_core", "context_assembly", "workflow",
                    "agent", "state", "tool_security", "governed_tool",
                    "evaluation", "response", "trace",
                ],
            )
            self.assertEqual(events[-1].stage, "trace")
            self.assertEqual(events[-1].status, "ok")

            context_keys = (
                "request_id", "session_id", "workflow_id",
                "task_id", "agent_id", "trace_id",
            )
            for event in events:
                self.assertTrue(all(key in event.metadata for key in context_keys))
            self.assertEqual(
                len({event.metadata["trace_id"] for event in events}),
                1,
            )

            stored = {item.key: item.value for item in memory.retrieve(events[0].metadata["session_id"])}
            self.assertEqual(stored["last_goal"], "production-like validation goal")
            self.assertEqual(stored["last_response"], response)

        self.assertNotEqual(first[2][0].metadata["trace_id"], second[2][0].metadata["trace_id"])
        self.assertEqual(
            first[2][-1].metadata["session_id"],
            "pv3-1",
        )
        self.assertEqual(
            second[2][-1].metadata["session_id"],
            "pv3-2",
        )


if __name__ == "__main__":
    unittest.main()
