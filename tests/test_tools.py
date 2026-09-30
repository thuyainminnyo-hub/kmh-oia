import unittest

from src.tools import ToolRegistry, ToolRequest


class ToolContractTests(unittest.TestCase):
    def test_registered_echo_returns_typed_result(self):
        result = ToolRegistry().execute(ToolRequest("echo", "hello"))
        self.assertTrue(result.success)
        self.assertEqual(result.output_text, "hello")
        self.assertEqual(result.reason, "tool executed")

    def test_unregistered_tool_returns_failed_result(self):
        result = ToolRegistry().execute(ToolRequest("shell", "hello"))
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "tool is not registered")


if __name__ == "__main__":
    unittest.main()
