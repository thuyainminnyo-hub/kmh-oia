import unittest

from src.components import ContextAssembly, GovernedTool, InputGateway, OIARuntime
from src.security import ToolSecurityPolicy
from src.state import StateStore


class ComponentBoundaryTests(unittest.TestCase):
    def test_gateway_rejects_empty_goal(self):
        with self.assertRaises(ValueError):
            InputGateway().accept(" ")

    def test_context_assembly_is_deterministic(self):
        context = InputGateway().accept("hello")
        self.assertEqual(ContextAssembly().build(context), {"goal": "hello"})

    def test_governed_tool_enforces_security(self):
        tool = GovernedTool(ToolSecurityPolicy())
        self.assertEqual(tool.execute("echo", "hello"), "hello")
        with self.assertRaises(PermissionError):
            tool.execute("shell", "hello")

    def test_runtime_composes_components(self):
        runtime = OIARuntime(state=StateStore())
        response, stages = runtime.execute("hello", session_id="s1")
        self.assertEqual(response, "hello")
        self.assertEqual(stages[-3:], ["evaluation", "response", "trace"])


if __name__ == "__main__":
    unittest.main()
