import json
import unittest
from decimal import Decimal

from src.agent import AgentRequest
from src.ai_contracts import (
    AIRequestGuardrail,
    AIBudgetPolicy,
    DataClassification,
    ModelRoute,
)
from src.components import OIARuntime
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.model_gateway import ModelGateway, ModelResponse, ModelUsage
from src.model_gateway_agent import GatewayBackedAgent


class CapturingProvider:
    def __init__(self, response_text):
        self.response_text = response_text
        self.calls = 0
        self.last_request = None

    def generate(self, request):
        self.calls += 1
        self.last_request = request
        return ModelResponse(self.response_text, ModelUsage(120, 32, Decimal("0")))


def make_runtime(tool_name="echo", input_text="hello from model"):
    provider = CapturingProvider(json.dumps({
        "tool_name": tool_name,
        "input_text": input_text,
        "reason": "model proposal; governed runtime must authorize",
    }))
    route = ModelRoute(
        route_id="local-free",
        provider="local",
        model="fake-local",
        free_tier=True,
        enabled=True,
        max_input_tokens=8000,
        max_output_tokens=256,
        allowed_data_classifications=(DataClassification.INTERNAL,),
    )
    gateway = ModelGateway(
        AIRequestGuardrail(
            [route],
            AIBudgetPolicy(max_request_input_tokens=8000, max_request_output_tokens=256),
        ),
        [route],
        {"local-free": provider},
    )
    agent = GatewayBackedAgent(gateway, route_id="local-free")
    return OIARuntime(agent=agent), provider


class ModelGatewayRuntimeIntegrationTests(unittest.TestCase):
    def test_model_agent_runs_through_live_governed_tool_path(self):
        runtime, provider = make_runtime()
        console = LiveOperatingConsole(
            date="2026-11-03",
            primary_objective="Verify model gateway integration",
        )
        command = console.add_command(
            objective="execute a low-risk local echo",
            priority="P1",
            owner="human + AI",
            expected_output="hello from model",
        )

        record = LiveRuntimeBridge(console, runtime=runtime).execute(command.id)

        self.assertEqual(record.final_status, "LEARNED")
        self.assertEqual(record.qa_status, "PASS")
        self.assertEqual(provider.calls, 1)
        self.assertIn("agent", record.trace_stages)
        self.assertIn("tool_security", record.trace_stages)
        self.assertIn("governed_tool", record.trace_stages)
        self.assertIn("evaluation", record.trace_stages)
        self.assertEqual(record.admission.evidence_status, "OBSERVED")
        self.assertFalse(record.admission.learning_admitted)
        self.assertNotIn(f'"session_id": "command:{command.id}"', provider.last_request.input_text)

    def test_model_proposed_unauthorized_tool_is_blocked_by_runtime(self):
        runtime, provider = make_runtime(tool_name="unlisted-tool")
        console = LiveOperatingConsole(
            date="2026-11-03",
            primary_objective="Verify deny by default",
        )
        command = console.add_command(
            objective="try an unlisted tool",
            priority="P1",
            owner="human + AI",
            expected_output="must be blocked",
        )

        with self.assertRaises(PermissionError):
            LiveRuntimeBridge(console, runtime=runtime).execute(command.id)

        self.assertEqual(provider.calls, 1)
        self.assertEqual(
            console.snapshot().commands[0].status,
            "BLOCKED",
        )


if __name__ == "__main__":
    unittest.main()
