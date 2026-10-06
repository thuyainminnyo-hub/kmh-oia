import unittest
from types import SimpleNamespace

from src.execution_identity import ExecutionIdentity, ExecutionIdentityContext
from src.real_execution_verification import RealExecutionVerificationEngine


class RealExecutionVerificationTests(unittest.TestCase):
    def setUp(self):
        self.identity = ExecutionIdentity(
            account_id="acct-1",
            instance_id="instance-1",
            environment_id="prod",
            session_id="session-1",
        )

    def record(self, *, qa="PASS", evidence=None, stages=None, response="done"):
        context = ExecutionIdentityContext(
            self.identity,
            "cmd-1",
            "exec-1",
        )
        return SimpleNamespace(
            execution_identity=context,
            operating_loop=None,
            trace_stages=tuple(stages or ("input", "output")),
            evidence=tuple(evidence or ("trace_id=trace-1", "response=done")),
            qa_status=qa,
            response=response,
        )

    def test_complete_runtime_record_is_verified(self):
        result = RealExecutionVerificationEngine().verify(self.record())
        self.assertTrue(result.verified)
        self.assertTrue(all(result.checks.values()))
        self.assertEqual(result.execution_id, "exec-1")

    def test_failed_qa_blocks_verification(self):
        result = RealExecutionVerificationEngine().verify(self.record(qa="FAIL"))
        self.assertFalse(result.verified)
        self.assertFalse(result.checks["qa"])

    def test_missing_identity_blocks_verification(self):
        record = self.record()
        record.execution_identity = None
        record.operating_loop = SimpleNamespace(execution_id="exec-1")
        result = RealExecutionVerificationEngine().verify(record)
        self.assertFalse(result.verified)
        self.assertFalse(result.checks["identity"])

    def test_missing_trace_evidence_blocks_verification(self):
        result = RealExecutionVerificationEngine().verify(
            self.record(evidence=("response=done",))
        )
        self.assertFalse(result.verified)
        self.assertFalse(result.checks["trace"])


if __name__ == "__main__":
    unittest.main()
