import unittest

from src.trace import ExecutionContext


class ExecutionContextTests(unittest.TestCase):
    def test_context_preserves_session_and_has_all_identifiers(self):
        context = ExecutionContext.create("session-a")
        self.assertEqual(context.session_id, "session-a")
        self.assertTrue(context.request_id)
        self.assertTrue(context.workflow_id)
        self.assertTrue(context.task_id)
        self.assertTrue(context.agent_id)
        self.assertTrue(context.trace_id)

    def test_context_ids_are_unique_per_execution(self):
        first = ExecutionContext.create("session-a")
        second = ExecutionContext.create("session-a")
        self.assertNotEqual(first.request_id, second.request_id)
        self.assertNotEqual(first.trace_id, second.trace_id)


if __name__ == "__main__": unittest.main()
