import unittest
from decimal import Decimal

from src.ai_contracts import (
    AIRequest,
    AIRequestGuardrail,
    AIBudgetPolicy,
    BudgetSnapshot,
    ModelRoute,
    TaskClass,
)
from src.model_gateway import (
    ModelGateway,
    ModelResponse,
    ModelUsage,
)
from src.trace import ExecutionContext, InMemoryTracer


class FakeProvider:
    def __init__(self, response=None, error=None):
        self.response = response or ModelResponse(
            "review complete", ModelUsage(80, 20, Decimal("0"))
        )
        self.error = error
        self.calls = 0

    def generate(self, request):
        self.calls += 1
        if self.error:
            raise self.error
        return self.response


def route(**overrides):
    values = dict(
        route_id="local-free",
        provider="local",
        model="fake-model",
        free_tier=True,
        enabled=True,
        max_input_tokens=500,
        max_output_tokens=200,
    )
    values.update(overrides)
    return ModelRoute(**values)


def request(**overrides):
    values = dict(
        request_id="r1",
        session_id="s1",
        task_class=TaskClass.CODE_REVIEW,
        input_text="review this",
        route_id="local-free",
        estimated_input_tokens=100,
        max_output_tokens=100,
    )
    values.update(overrides)
    return AIRequest(**values)


class ModelGatewayTests(unittest.TestCase):
    def setUp(self):
        self.route = route()
        self.provider = FakeProvider()
        self.guard = AIRequestGuardrail([self.route])
        self.tracer = InMemoryTracer()
        self.gateway = ModelGateway(
            self.guard, [self.route], {"local-free": self.provider}, self.tracer
        )
        self.context = ExecutionContext.create("s1")

    def test_admitted_request_calls_registered_provider(self):
        result = self.gateway.execute(request(), context=self.context)
        self.assertTrue(result.accepted)
        self.assertEqual(result.text, "review complete")
        self.assertEqual(self.provider.calls, 1)
        self.assertEqual(len(self.tracer.events), 2)
        self.tracer.validate_integrity()

    def test_denied_request_never_calls_provider(self):
        result = self.gateway.execute(request(route_id="unknown"))
        self.assertFalse(result.accepted)
        self.assertEqual(self.provider.calls, 0)

    def test_missing_adapter_fails_closed(self):
        gateway = ModelGateway(self.guard, [self.route], {})
        result = gateway.execute(request())
        self.assertFalse(result.accepted)
        self.assertIn("no provider adapter", result.reason)

    def test_provider_exception_is_contained(self):
        provider = FakeProvider(error=RuntimeError("private provider detail"))
        gateway = ModelGateway(self.guard, [self.route], {"local-free": provider})
        result = gateway.execute(request())
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "provider execution failed")
        self.assertNotIn("private provider detail", result.reason)

    def test_invalid_response_contract_is_rejected(self):
        provider = FakeProvider(response={"text": "not typed"})
        gateway = ModelGateway(self.guard, [self.route], {"local-free": provider})
        self.assertFalse(gateway.execute(request()).accepted)

    def test_empty_response_is_rejected(self):
        provider = FakeProvider(response=ModelResponse(
            " ", ModelUsage(10, 10)
        ))
        gateway = ModelGateway(self.guard, [self.route], {"local-free": provider})
        self.assertFalse(gateway.execute(request()).accepted)

    def test_output_usage_over_limit_is_rejected(self):
        provider = FakeProvider(response=ModelResponse(
            "too much", ModelUsage(10, 101)
        ))
        gateway = ModelGateway(self.guard, [self.route], {"local-free": provider})
        self.assertFalse(gateway.execute(request()).accepted)

    def test_input_usage_over_estimate_is_rejected(self):
        provider = FakeProvider(response=ModelResponse(
            "unexpected", ModelUsage(101, 10)
        ))
        gateway = ModelGateway(self.guard, [self.route], {"local-free": provider})
        self.assertFalse(gateway.execute(request()).accepted)

    def test_free_route_with_actual_cost_is_rejected(self):
        provider = FakeProvider(response=ModelResponse(
            "unexpected cost", ModelUsage(10, 10, Decimal("0.01"))
        ))
        gateway = ModelGateway(self.guard, [self.route], {"local-free": provider})
        self.assertFalse(gateway.execute(request()).accepted)

    def test_trace_contains_no_prompt_or_response_content(self):
        self.gateway.execute(request(), context=self.context)
        for event in self.tracer.events:
            self.assertNotIn("review this", str(event.metadata))
            self.assertNotIn("review complete", str(event.metadata))

    def test_duplicate_route_registration_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate gateway route_id"):
            ModelGateway(self.guard, [self.route, self.route], {})

    def test_unknown_provider_route_registration_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown route"):
            ModelGateway(self.guard, [self.route], {"other": self.provider})


if __name__ == "__main__":
    unittest.main()
