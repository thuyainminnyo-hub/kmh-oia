import unittest

from src.components import OIARuntime
from src.security import ToolSecurityPolicy
from src.tools import ToolRegistry


class RecordingRegistry(ToolRegistry):
    def __init__(self):
        super().__init__()
        self.executions = 0

    def execute(self, request):
        self.executions += 1
        return super().execute(request)


class Stage12SecurityValidationTests(unittest.TestCase):
    def test_pv6_allowlisted_tool_executes_and_unlisted_tool_is_denied(self):
        runtime = OIARuntime(
            security=ToolSecurityPolicy(allowed_tools={"echo"}),
        )

        response, _, events = runtime.execute_detailed(
            "security validation",
            session_id="pv6-allowed",
            tool_name="echo",
        )

        self.assertEqual(response, "security validation")
        security_event = next(event for event in events if event.stage == "tool_security")
        self.assertEqual(security_event.status, "ok")

        with self.assertRaises(PermissionError):
            runtime.execute_detailed(
                "security validation blocked",
                session_id="pv6-blocked",
                tool_name="admin",
            )

        error = runtime.tracer.events[-1]
        self.assertEqual(error.stage, "error")
        self.assertEqual(error.metadata["status"], "authorization")

    def test_pv6_denial_occurs_before_executor(self):
        registry = RecordingRegistry()
        runtime = OIARuntime(
            security=ToolSecurityPolicy(allowed_tools={"echo"}),
            registry=registry,
        )

        with self.assertRaises(PermissionError):
            runtime.execute_detailed(
                "blocked execution",
                session_id="pv6-pre-execution",
                tool_name="admin",
            )

        self.assertEqual(registry.executions, 0)

    def test_pv6_empty_tool_name_is_denied(self):
        runtime = OIARuntime(
            security=ToolSecurityPolicy(allowed_tools={"echo"}),
        )

        with self.assertRaises(PermissionError):
            runtime.execute_detailed(
                "empty tool validation",
                session_id="pv6-empty",
                tool_name="",
            )

        self.assertEqual(runtime.tracer.events[-1].metadata["status"], "authorization")


if __name__ == "__main__":
    unittest.main()
