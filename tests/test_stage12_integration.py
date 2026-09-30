import unittest

from src.agent import AgentDecision
from src.components import OIARuntime
from src.knowledge import KnowledgeItem, StaticKnowledgeSource
from src.memory import InMemoryMemoryStore
from src.security import ToolSecurityPolicy


class IntegrationAgent:
    def __init__(self):
        self.request = None

    def decide(self, request):
        self.request = request
        return AgentDecision("echo", request.goal, "stage-12 integration validation")


class Stage12IntegrationValidationTests(unittest.TestCase):
    def test_pv2_cross_module_contracts_and_context_propagation(self):
        memory = InMemoryMemoryStore()
        knowledge = StaticKnowledgeSource([
            KnowledgeItem("integration-source", "Stage 12 integration evidence"),
        ])
        agent = IntegrationAgent()
        runtime = OIARuntime(memory=memory, knowledge=knowledge, agent=agent)

        response, stages, events = runtime.execute_detailed(
            "integration validation goal",
            session_id="pv2",
        )

        self.assertEqual(response, "integration validation goal")
        self.assertIn("context_assembly", stages)
        self.assertIn("workflow", stages)
        self.assertIn("agent", stages)
        self.assertIn("governed_tool", stages)
        self.assertIn("evaluation", stages)

        self.assertEqual(agent.request.context["memory"], [])
        self.assertIn("integration-source", agent.request.context["knowledge"])

        by_stage = {event.stage: event for event in events}
        self.assertEqual(by_stage["tool_security"].status, "ok")
        self.assertEqual(by_stage["governed_tool"].status, "ok")
        self.assertEqual(by_stage["evaluation"].status, "ok")
        self.assertEqual(by_stage["response"].metadata["memory_updated"], "true")

        context_keys = ("request_id", "session_id", "workflow_id", "task_id", "agent_id", "trace_id")
        contexts = [{key: event.metadata[key] for key in context_keys} for event in events]
        self.assertTrue(all(context == contexts[0] for context in contexts))
        self.assertEqual(contexts[0]["session_id"], "pv2")

        stored = {item.key: item.value for item in memory.retrieve("pv2")}
        self.assertEqual(stored["last_goal"], "integration validation goal")
        self.assertEqual(stored["last_response"], response)

    def test_pv2_security_contract_blocks_disallowed_tool_before_execution(self):
        runtime = OIARuntime(
            security=ToolSecurityPolicy(allowed_tools={"not-echo"}),
        )

        with self.assertRaises(PermissionError):
            runtime.execute("integration security boundary", session_id="pv2-security", tool_name="echo")

        error = runtime.tracer.events[-1]
        self.assertEqual(error.stage, "error")
        self.assertEqual(error.metadata["status"], "authorization")


if __name__ == "__main__":
    unittest.main()
