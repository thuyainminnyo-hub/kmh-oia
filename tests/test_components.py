import unittest

from src.agent import AgentDecision, AgentRequest
from src.components import ContextAssembly, GovernedTool, InputGateway, OIARuntime
from src.evaluation import EvaluationResult
from src.response import Response
from src.security import ToolSecurityPolicy
from src.state import StateStore
from src.tools import ToolRequest, ToolResult
from src.workflow import DeterministicOIACore, DeterministicWorkflow

class FakeToolExecutor:
    def execute(self, request: ToolRequest) -> ToolResult:
        return ToolResult(request.tool_name, f"fake:{request.input_text}", True, "fake executor")
class FakeAgent:
    def decide(self, request: AgentRequest) -> AgentDecision:
        return AgentDecision("echo", f"planned:{request.goal}", "test agent")
class FakeEvaluator:
    def evaluate(self, result: ToolResult) -> EvaluationResult:
        return EvaluationResult(True, "test evaluator accepted")
class RejectingEvaluator:
    def evaluate(self, result: ToolResult) -> EvaluationResult:
        return EvaluationResult(False, "test evaluator rejected")
class FakeResponder:
    def render(self, text: str) -> Response:
        return Response(text=f"response:{text}")
class FakeCore:
    def build_context(self, goal: str) -> dict[str, str]:
        return {"goal": f"core:{goal}"}
class FakeWorkflow:
    def prepare(self, context: dict[str, str]) -> AgentRequest:
        return AgentRequest(f"workflow:{context['goal']}")

class ComponentBoundaryTests(unittest.TestCase):
    def test_gateway_rejects_empty_goal(self):
        with self.assertRaises(ValueError): InputGateway().accept(" ")
    def test_context_assembly_is_deterministic(self):
        context = InputGateway().accept("hello")
        self.assertEqual(ContextAssembly().build(context), {"goal": "hello"})
    def test_core_and_workflow_are_deterministic(self):
        context = DeterministicOIACore().build_context("hello")
        request = DeterministicWorkflow().prepare(context)
        self.assertEqual(context, {"goal": "hello"})
        self.assertEqual(request.goal, "hello")
    def test_runtime_accepts_interchangeable_core_and_workflow(self):
        response, _, events = OIARuntime(state=StateStore(), core=FakeCore(), workflow=FakeWorkflow()).execute_detailed("hello")
        self.assertEqual(response, "workflow:core:hello")
        self.assertEqual(next(e for e in events if e.stage == "agent").metadata["reason"], "deterministic default policy")
    def test_governed_tool_enforces_security(self):
        tool = GovernedTool(ToolSecurityPolicy())
        result = tool.execute(ToolRequest("echo", "hello"))
        self.assertTrue(result.success); self.assertEqual(result.output_text, "hello")
        blocked = tool.execute(ToolRequest("shell", "hello"))
        self.assertFalse(blocked.success); self.assertEqual(blocked.reason, "tool is not allowlisted")
    def test_governed_tool_accepts_interchangeable_executor(self):
        result = GovernedTool(ToolSecurityPolicy(), FakeToolExecutor()).execute(ToolRequest("echo", "hello"))
        self.assertTrue(result.success); self.assertEqual(result.output_text, "fake:hello")
    def test_runtime_accepts_interchangeable_agent(self):
        response, _, events = OIARuntime(state=StateStore(), agent=FakeAgent()).execute_detailed("hello", tool_name=None)
        self.assertEqual(response, "planned:hello")
        self.assertEqual(next(e for e in events if e.stage == "agent").metadata["reason"], "test agent")
    def test_runtime_accepts_interchangeable_evaluator(self):
        response, _, events = OIARuntime(state=StateStore(), evaluator=FakeEvaluator()).execute_detailed("hello")
        self.assertEqual(response, "hello")
        self.assertEqual(next(e for e in events if e.stage == "evaluation").metadata["reason"], "test evaluator accepted")
    def test_runtime_stops_on_rejected_evaluation(self):
        with self.assertRaisesRegex(ValueError, "test evaluator rejected"):
            OIARuntime(state=StateStore(), evaluator=RejectingEvaluator()).execute_detailed("hello")
    def test_runtime_accepts_interchangeable_responder(self):
        response, _, events = OIARuntime(state=StateStore(), responder=FakeResponder()).execute_detailed("hello")
        self.assertEqual(response, "response:hello")
        self.assertEqual(next(e for e in events if e.stage == "response").status, "ok")
    def test_runtime_composes_components(self):
        response, stages = OIARuntime(state=StateStore()).execute("hello", session_id="s1")
        self.assertEqual(response, "hello"); self.assertEqual(stages[-3:], ["evaluation", "response", "trace"])
    def test_runtime_emits_structured_events(self):
        response, stages, events = OIARuntime(state=StateStore()).execute_detailed("hello", session_id="s1")
        self.assertEqual(response, "hello"); self.assertEqual([event.stage for event in events], stages)
        evaluation = next(event for event in events if event.stage == "evaluation")
        self.assertEqual(evaluation.status, "ok"); self.assertEqual(evaluation.metadata["reason"], "tool result accepted")

if __name__ == "__main__": unittest.main()
