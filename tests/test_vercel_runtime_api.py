import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from src.index import ExecutionRequest, create_execution, health, readiness


class VercelRuntimeApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_health_is_public_and_does_not_disclose_configuration(self) -> None:
        result = health()
        self.assertEqual(result["status"], "ok")
        self.assertNotIn("api_key", result)

    def test_readiness_reports_closed_gate_by_default(self) -> None:
        result = readiness()
        self.assertEqual(result["execution_gate"], "closed")
        self.assertFalse(result["execution_enabled"])
        self.assertFalse(result["api_key_configured"])
        self.assertEqual(result["state_backend"], "ephemeral-per-request")
        self.assertFalse(result["production_release_authorized"])

    def test_missing_api_key_configuration_fails_closed(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            create_execution(ExecutionRequest(goal="test"), "any-value")
        self.assertEqual(caught.exception.status_code, 503)
        self.assertEqual(caught.exception.detail, "api_auth_not_configured")

    def test_invalid_api_key_is_rejected(self) -> None:
        os.environ["KMH_OIA_API_KEY"] = "expected-secret"
        os.environ["KMH_OIA_EXECUTION_ENABLED"] = "true"
        with self.assertRaises(HTTPException) as caught:
            create_execution(ExecutionRequest(goal="test"), "wrong-secret")
        self.assertEqual(caught.exception.status_code, 401)

    def test_execution_flag_remains_closed_without_explicit_enablement(self) -> None:
        os.environ["KMH_OIA_API_KEY"] = "expected-secret"
        with self.assertRaises(HTTPException) as caught:
            create_execution(ExecutionRequest(goal="test"), "expected-secret")
        self.assertEqual(caught.exception.status_code, 503)
        self.assertEqual(caught.exception.detail, "execution_disabled")

    def test_restricted_deterministic_execution_returns_trace(self) -> None:
        os.environ["KMH_OIA_API_KEY"] = "expected-secret"
        os.environ["KMH_OIA_EXECUTION_ENABLED"] = "true"
        result = create_execution(ExecutionRequest(goal="hello OIA"), "expected-secret")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["mode"], "deterministic_local_only")
        self.assertEqual(result["response"], "hello OIA")
        self.assertTrue(result["execution_id"])
        self.assertTrue(result["trace_id"])
        self.assertTrue(result["events"])
        self.assertEqual(result["durability"], "not_persisted")
        self.assertFalse(result["external_side_effects"])

    def test_unknown_request_fields_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ExecutionRequest.model_validate(
                {"goal": "test", "tool_name": "shell"}
            )

    def test_blank_goal_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ExecutionRequest(goal="   ")


if __name__ == "__main__":
    unittest.main()
