import unittest

from src.agent import AgentDecision, AgentRequest
from src.components import ContextAssembly, GovernedTool, InputGateway, OIARuntime, RuntimeContext
from src.evaluation import EvaluationResult
from src.response import Response
from src.security import ToolSecurityPolicy
from src.state import StateStore
from src.tools import ToolRequest, ToolResult
from src.workflow import DeterministicOIACore, DeterministicWorkflow

class FakeToolExecutor:
    def execute(self, request: ToolRequest) -> ToolResult: return ToolResult(request.tool_name, f"fake:{request.input_text}", True, "fake executor")
class FakeAgent:
    def decide(self, request: AgentRequest) -> AgentDecision: return AgentDecision("echo", f"planned:{request.goal}", "test agent")
class FakeEvaluator:
    def evaluate(self, result: ToolResult) -> EvaluationResult: return EvaluationResult(True, "accepted")
class FakeResponder:
    def render(self, text: str) -> Response: return Response(text)
class FakeGateway:
    def accept(self, goal: str) -> RuntimeContext: return RuntimeContext(f"gateway:{goal}")
class FakeContextAssembly:
    def build(self, context: RuntimeContext) -> dict[str, str]: return {"goal": f"context:{context.goal}"}

class ComponentBoundaryTests(unittest.TestCase):
    def test_gateway_rejects_empty_goal(self):
        with self.assertRaises(ValueError): InputGateway().accept(" ")
    def test_context_assembly_is_deterministic(self):
        context = InputGateway().accept("hello")
        self.assertEqual(ContextAssembly().build(context), {"goal": "hello"})
    def test_core_and_workflow_are_deterministic(self):
        context = DeterministicOIACore().build_context("hello")
        request = DeterministicWorkflow().prepare(context)
        self.assertEqual(context, {"goal": "hello"}); self.assertEqual(request.goal, "hello")
    def test_runtime_accepts_interchangeable_gateway_and_context(self):
        response, _, events = OIARuntime(state=StateStore(), gateway=FakeGateway(), context_assembly=FakeContextAssembly(), agent=FakeAgent(), evaluator=FakeEvaluator(), responder=FakeResponder()).execute_detailed("hello")
        self.assertEqual(response, "planned:context:gateway:hello")
        self.assertEqual(next(e for e in events if e.stage == "agent").metadata["reason"], "test agent")
    def test_runtime_accepts_interchangeable_core_and_workflow(self):
        response, _, events = OIARuntime(state=StateStore(), core=lambda: None if False else None, workflow=DeterministicWorkflow()).execute_detailed("hello")
        self.assertEqual(response, "hello")
    def test_governed_tool_enforces_security(self):
        tool = GovernedTool(ToolSecurityPolicy()); result = tool.execute(ToolRequest("echo", "hello"))
        self.assertTrue(result.success); self.assertEqual(result.output_text, "hello")
        blocked = tool.execute(ToolRequest("shell", "hello")); self.assertFalse(blocked.success)
    def test_governed_tool_accepts_interchangeable_executor(self):
        result = GovernedTool(ToolSecurityPolicy(), FakeToolExecutor()).execute(ToolRequest("echo", "hello"))
        self.assertTrue(result.success); self.assertEqual(result.output_text, "fake:hello")
    def test_runtime_composes_components(self):
        response, stages = OIARuntime(state=StateStore()).execute("hello", session_id="s1")
        self.assertEqual(response, "hello"); self.assertEqual(stages[-3:], ["evaluation", "response", "trace"])

if __name__ == "__main__": unittest.main()
