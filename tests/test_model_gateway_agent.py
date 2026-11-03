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
from src.model_gateway import ModelGateway, ModelResponse, ModelUsage
from src.model_gateway_agent import GatewayBackedAgent


class FakeProvider:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        return self.response


def build_agent(response_text):
    route = ModelRoute(
        route_id="local-free",
        provider="local",
        model="fake",
        free_tier=True,
        enabled=True,
        max_input_tokens=8000,
        max_output_tokens=256,
        allowed_data_classifications=(DataClassification.INTERNAL,),
    )
    provider = FakeProvider(ModelResponse(
        response_text, ModelUsage(100, 30, Decimal("0"))
    ))
    gateway = ModelGateway(
        AIRequestGuardrail([route], AIBudgetPolicy(max_request_input_tokens=8000)),
        [route],
        {"local-free": provider},
    )
    return GatewayBackedAgent(gateway, route_id="local-free"), provider


class GatewayBackedAgentTests(unittest.TestCase):
    def test_valid_model_plan_becomes_agent_decision(self):
        agent, provider = build_agent(json.dumps({
            "tool_name": "echo",
            "input_text": "hello",
            "reason": "low-risk local action",
        }))
        decision = agent.decide(AgentRequest("say hello", {"goal": "say hello"}))
        self.assertEqual(decision.tool_name, "echo")
        self.assertEqual(decision.input_text, "hello")
        self.assertEqual(provider.calls, 1)

    def test_gateway_denial_fails_closed(self):
        agent, provider = build_agent(json.dumps({
            "tool_name": "echo", "input_text": "hello", "reason": "test"
        }))
        agent._route_id = "not-allowlisted"
        with self.assertRaisesRegex(PermissionError, "gateway denied"):
            agent.decide(AgentRequest("say hello"))
        self.assertEqual(provider.calls, 0)

    def test_invalid_json_is_rejected(self):
        agent, _ = build_agent("not-json")
        with self.assertRaisesRegex(ValueError, "valid JSON"):
            agent.decide(AgentRequest("goal"))

    def test_extra_response_field_is_rejected(self):
        agent, _ = build_agent(json.dumps({
            "tool_name": "echo", "input_text": "hello", "reason": "test",
            "execute_now": True,
        }))
        with self.assertRaisesRegex(ValueError, "exactly"):
            agent.decide(AgentRequest("goal"))

    def test_empty_response_field_is_rejected(self):
        agent, _ = build_agent(json.dumps({
            "tool_name": "echo", "input_text": "", "reason": "test"
        }))
        with self.assertRaisesRegex(ValueError, "non-empty"):
            agent.decide(AgentRequest("goal"))

    def test_model_selected_tool_is_only_a_proposal(self):
        # This adapter only returns AgentDecision. OIARuntime remains the
        # authority that applies AutonomyPolicy and GovernedTool security.
        agent, _ = build_agent(json.dumps({
            "tool_name": "unlisted-tool", "input_text": "payload", "reason": "proposal"
        }))
        decision = agent.decide(AgentRequest("goal"))
        self.assertEqual(decision.tool_name, "unlisted-tool")


if __name__ == "__main__":
    unittest.main()
