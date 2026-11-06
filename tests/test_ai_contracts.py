import unittest
from decimal import Decimal

from src.ai_contracts import (
    AIRequest,
    AIRequestGuardrail,
    AIBudgetPolicy,
    BudgetSnapshot,
    DataClassification,
    ModelRoute,
    TaskClass,
)


def request(**overrides):
    values = {
        "request_id": "req-1",
        "session_id": "session-1",
        "task_class": TaskClass.CODE_REVIEW,
        "input_text": "Review this small patch",
        "route_id": "local-free",
        "estimated_input_tokens": 100,
        "max_output_tokens": 200,
    }
    values.update(overrides)
    return AIRequest(**values)


def free_route(**overrides):
    values = {
        "route_id": "local-free",
        "provider": "local",
        "model": "test-model",
        "free_tier": True,
        "enabled": True,
        "max_input_tokens": 1_000,
        "max_output_tokens": 500,
    }
    values.update(overrides)
    return ModelRoute(**values)


class AIRequestContractTests(unittest.TestCase):
    def test_mapping_parser_accepts_valid_payload(self):
        parsed = AIRequest.from_mapping({
            "request_id": "r1",
            "session_id": "s1",
            "task_class": "code_assist",
            "input_text": "hello",
            "route_id": "local-free",
            "estimated_input_tokens": 3,
            "max_output_tokens": 20,
        })
        self.assertEqual(parsed.task_class, TaskClass.CODE_ASSIST)
        self.assertEqual(parsed.data_classification, DataClassification.INTERNAL)

    def test_mapping_parser_rejects_unknown_fields(self):
        with self.assertRaisesRegex(ValueError, "unknown request fields"):
            AIRequest.from_mapping({
                "request_id": "r1", "session_id": "s1",
                "task_class": "code_assist", "input_text": "x",
                "route_id": "local-free", "estimated_input_tokens": 1,
                "max_output_tokens": 1, "execute_shell": True,
            })

    def test_mapping_parser_rejects_missing_fields(self):
        with self.assertRaisesRegex(ValueError, "missing request fields"):
            AIRequest.from_mapping({"request_id": "r1"})

    def test_mapping_parser_rejects_unknown_task(self):
        payload = {
            "request_id": "r1", "session_id": "s1",
            "task_class": "unrestricted", "input_text": "x",
            "route_id": "local-free", "estimated_input_tokens": 1,
            "max_output_tokens": 1,
        }
        with self.assertRaisesRegex(ValueError, "invalid task"):
            AIRequest.from_mapping(payload)

    def test_request_rejects_boolean_token_count(self):
        with self.assertRaisesRegex(ValueError, "non-negative integer"):
            request(estimated_input_tokens=True)

    def test_request_rejects_negative_token_count(self):
        with self.assertRaisesRegex(ValueError, "non-negative integer"):
            request(estimated_input_tokens=-1)

    def test_request_rejects_zero_output_budget(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            request(max_output_tokens=0)

    def test_request_rejects_non_finite_cost(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            request(estimated_cost_usd=Decimal("NaN"))


class AIRequestGuardrailTests(unittest.TestCase):
    def setUp(self):
        self.guard = AIRequestGuardrail([free_route()])

    def test_valid_free_route_is_admitted_without_provider_call(self):
        decision = self.guard.evaluate(request())
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reserved_tokens, 300)
        self.assertIn("provider execution is not performed", decision.reason)

    def test_unknown_route_is_rejected(self):
        self.assertFalse(self.guard.evaluate(request(route_id="unknown")).allowed)

    def test_disabled_route_is_rejected(self):
        guard = AIRequestGuardrail([free_route(enabled=False)])
        self.assertEqual(guard.evaluate(request()).reason, "route is disabled")

    def test_paid_route_is_denied_by_default(self):
        paid = free_route(route_id="paid", free_tier=False)
        guard = AIRequestGuardrail([paid])
        decision = guard.evaluate(request(route_id="paid", estimated_cost_usd=Decimal("0.01")))
        self.assertEqual(decision.reason, "paid routes are disabled by policy")

    def test_free_route_cannot_claim_nonzero_cost(self):
        decision = self.guard.evaluate(request(estimated_cost_usd=Decimal("0.01")))
        self.assertEqual(decision.reason, "free-tier route must have zero estimated cost")

    def test_confidential_data_is_denied_by_default(self):
        decision = self.guard.evaluate(
            request(data_classification=DataClassification.CONFIDENTIAL)
        )
        self.assertIn("data classification", decision.reason)

    def test_explicitly_approved_confidential_route_can_be_admitted(self):
        route = free_route(
            allowed_data_classifications=(
                DataClassification.PUBLIC,
                DataClassification.INTERNAL,
                DataClassification.CONFIDENTIAL,
            )
        )
        guard = AIRequestGuardrail([route])
        self.assertTrue(guard.evaluate(
            request(data_classification=DataClassification.CONFIDENTIAL)
        ).allowed)

    def test_input_character_limit_is_enforced(self):
        guard = AIRequestGuardrail(
            [free_route()], AIBudgetPolicy(max_input_chars=5)
        )
        self.assertEqual(guard.evaluate(request(input_text="too long")).reason,
                         "input exceeds character limit")

    def test_input_token_limit_is_enforced(self):
        guard = AIRequestGuardrail([free_route()], AIBudgetPolicy(max_request_input_tokens=50))
        self.assertEqual(guard.evaluate(request(estimated_input_tokens=51)).reason,
                         "input token limit exceeded")

    def test_route_output_limit_is_enforced(self):
        self.assertEqual(self.guard.evaluate(request(max_output_tokens=501)).reason,
                         "output token limit exceeded")

    def test_session_token_budget_is_enforced(self):
        guard = AIRequestGuardrail([free_route()], AIBudgetPolicy(max_session_tokens=250))
        decision = guard.evaluate(request(), BudgetSnapshot(session_tokens_used=1))
        self.assertEqual(decision.reason, "session token budget exceeded")

    def test_session_cost_budget_is_enforced(self):
        paid = free_route(route_id="paid", free_tier=False)
        policy = AIBudgetPolicy(
            allow_paid_routes=True,
            max_session_cost_usd=Decimal("0.10"),
        )
        guard = AIRequestGuardrail([paid], policy)
        req = request(route_id="paid", estimated_cost_usd=Decimal("0.05"))
        decision = guard.evaluate(req, BudgetSnapshot(
            session_cost_usd=Decimal("0.06")
        ))
        self.assertEqual(decision.reason, "session cost budget exceeded")

    def test_invalid_budget_snapshot_fails_closed(self):
        decision = self.guard.evaluate(request(), budget=None)
        self.assertTrue(decision.allowed)
        invalid = self.guard.evaluate(request(), budget="not-a-budget")
        self.assertFalse(invalid.allowed)

    def test_duplicate_route_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate route_id"):
            AIRequestGuardrail([free_route(), free_route()])

    def test_paid_route_requires_explicit_policy_opt_in(self):
        paid = free_route(route_id="paid", free_tier=False)
        guard = AIRequestGuardrail(
            [paid],
            AIBudgetPolicy(
                allow_paid_routes=True,
                max_session_cost_usd=Decimal("1.00"),
            ),
        )
        decision = guard.evaluate(
            request(route_id="paid", estimated_cost_usd=Decimal("0.10"))
        )
        self.assertTrue(decision.allowed)


if __name__ == "__main__":
    unittest.main()
