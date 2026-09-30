import unittest

from src.components import ContextAssembly, GovernedTool, InputGateway, OIARuntime
from src.security import ToolSecurityPolicy
from src.state import StateStore
from src.tools import ToolRequest


class ComponentBoundaryTests(unittest.TestCase):
    def test_gateway_rejects_empty_goal(self):
        with self.assertRaises(ValueError):
            InputGateway().accept(" ")

    def test_context_assembly_is_deterministic(self):
        context = InputGateway().accept("hello")
        self.assertEqual(ContextAssembly().build(context), {"goal": "hello"})

    def test_governed_tool_enforces_security(self):
        tool = GovernedTool(ToolSecurityPolicy())
        result = tool.execute(ToolRequest("echo", "hello"))
        self.assertTrue(result.success)
        self.assertEqual(result.output_text, "hello")
        blocked = tool.execute(ToolRequest("shell", "hello"))
        self.assertFalse(blocked.success)
        self.assertEqual(blocked.reason, "tool is not allowlisted")

    def test_runtime_composes_components(self):
        runtime = OIARuntime(state=StateStore())
        response, stages = runtime.execute("hello", session_id="s1")
        self.assertEqual(response, "hello")
        self.assertEqual(stages[-3:], ["evaluation", "response", "trace"])

    def test_runtime_emits_structured_events(self):
        runtime = OIARuntime(state=StateStore())
        response, stages, events = runtime.execute_detailed("hello", session_id="s1")
        self.assertEqual(response, "hello")
        self.assertEqual([event.stage for event in events], stages)
        tool_event = next(event for event in events if event.stage == "tool_security")
        self.assertEqual(tool_event.status, "ok")
        self.assertEqual(tool_event.metadata["tool"], "echo")
        self.assertEqual(tool_event.metadata["reason"], "tool executed")


if __name__ == "__main__":
    unittest.main()
