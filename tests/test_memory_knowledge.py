import unittest

from src.agent import AgentDecision
from src.components import OIARuntime
from src.knowledge import KnowledgeItem, StaticKnowledgeSource
from src.memory import InMemoryMemoryStore, MemoryEntry


class CapturingAgent:
    def __init__(self):
        self.requests = []

    def decide(self, request):
        self.requests.append(request)
        return AgentDecision("echo", request.goal, "captured context")


class FakeMemory:
    def __init__(self):
        self.entries = [MemoryEntry("preference", "concise")]
        self.updates = []

    def retrieve(self, session_id):
        return list(self.entries)

    def update(self, session_id, key, value):
        self.updates.append((session_id, key, value))

    def snapshot(self, session_id):
        return list(self.entries)

    def restore(self, session_id, snapshot):
        self.entries = list(snapshot)


class MemoryKnowledgeIntegrationTests(unittest.TestCase):
    def test_context_contains_memory_and_knowledge_for_agent(self):
        memory = FakeMemory()
        knowledge = StaticKnowledgeSource([KnowledgeItem("test-source", "OIA integration evidence")])
        agent = CapturingAgent()
        response, _, _ = OIARuntime(memory=memory, knowledge=knowledge, agent=agent).execute_detailed("OIA integration")
        self.assertEqual(response, "OIA integration")
        context = agent.requests[0].context
        self.assertIn("preference=concise", context["memory"])
        self.assertIn("test-source", context["knowledge"])

    def test_memory_updates_after_runtime_execution(self):
        memory = InMemoryMemoryStore()
        runtime = OIARuntime(memory=memory)
        runtime.execute("hello", session_id="session-a")
        entries = {item.key: item.value for item in memory.retrieve("session-a")}
        self.assertEqual(entries["last_goal"], "hello")
        self.assertEqual(entries["last_response"], "hello")

    def test_memory_isolated_by_session(self):
        memory = InMemoryMemoryStore()
        runtime = OIARuntime(memory=memory)
        runtime.execute("alpha", session_id="a")
        self.assertEqual(memory.retrieve("b"), [])


if __name__ == "__main__":
    unittest.main()
