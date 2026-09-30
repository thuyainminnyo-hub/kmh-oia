import unittest

from src.agent import AgentDecision
from src.components import OIARuntime
from src.knowledge import KnowledgeItem, StaticKnowledgeSource
from src.memory import InMemoryMemoryStore


class EvidenceAgent:
    def __init__(self) -> None:
        self.request = None

    def decide(self, request):
        self.request = request
        return AgentDecision("echo", request.goal, "stage-11 acceptance agent")


class Stage11EndToEndTests(unittest.TestCase):
    def test_complete_text_runtime_with_retrieval_governance_evaluation_memory_and_trace(self):
        memory = InMemoryMemoryStore()
        knowledge = StaticKnowledgeSource([
            KnowledgeItem("acceptance-source", "KMH OIA Stage 11 governed tool evidence"),
        ])
        agent = EvidenceAgent()
        runtime = OIARuntime(memory=memory, knowledge=knowledge, agent=agent)

        response, stages, events = runtime.execute_detailed(
            "KMH OIA Stage 11 governed tool evidence",
            session_id="stage11-e2e",
        )

        self.assertEqual(response, "KMH OIA Stage 11 governed tool evidence")
        self.assertEqual(
            stages,
            [
                "input_gateway",
                "oia_core",
                "context_assembly",
                "workflow",
                "agent",
                "state",
                "tool_security",
                "governed_tool",
                "evaluation",
                "response",
                "trace",
            ],
        )

        self.assertIsNotNone(agent.request)
        self.assertIn("acceptance-source", agent.request.context["knowledge"])

        by_stage = {event.stage: event for event in events}
        self.assertEqual(by_stage["tool_security"].status, "ok")
        self.assertEqual(by_stage["evaluation"].status, "ok")
        self.assertEqual(by_stage["response"].metadata["memory_updated"], "true")
        self.assertEqual(by_stage["trace"].metadata["session_id"], "stage11-e2e")

        stored = {item.key: item.value for item in memory.retrieve("stage11-e2e")}
        self.assertEqual(stored["last_goal"], "KMH OIA Stage 11 governed tool evidence")
        self.assertEqual(stored["last_response"], response)

        context_ids = {
            event.metadata["request_id"],
            event.metadata["session_id"],
            event.metadata["workflow_id"],
            event.metadata["task_id"],
            event.metadata["agent_id"],
            event.metadata["trace_id"],
        }
        self.assertEqual(context_ids.__len__(), 6)
        for event in events:
            self.assertEqual(
                {key: event.metadata[key] for key in (
                    "request_id", "session_id", "workflow_id",
                    "task_id", "agent_id", "trace_id"
                )},
                {
                    key: events[0].metadata[key] for key in (
                        "request_id", "session_id", "workflow_id",
                        "task_id", "agent_id", "trace_id"
                    )
                },
            )


if __name__ == "__main__":
    unittest.main()
