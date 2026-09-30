import unittest

from src.errors import DeterministicErrorBoundary, ErrorCategory, ErrorBoundary


class FakeBoundary:
    def classify(self, error: Exception):
        return DeterministicErrorBoundary().classify(error)


class ErrorBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.boundary = DeterministicErrorBoundary()

    def test_validation_error(self):
        result = self.boundary.classify(ValueError("goal must not be empty"))
        self.assertEqual(result.category, ErrorCategory.VALIDATION)
        self.assertFalse(result.recoverable)

    def test_authorization_error(self):
        result = self.boundary.classify(PermissionError("tool is not allowlisted"))
        self.assertEqual(result.category, ErrorCategory.AUTHORIZATION)
        self.assertFalse(result.recoverable)

    def test_unknown_error_is_internal(self):
        result = self.boundary.classify(RuntimeError("unexpected"))
        self.assertEqual(result.category, ErrorCategory.INTERNAL)
        self.assertFalse(result.recoverable)

    def test_structural_contract(self):
        boundary: ErrorBoundary = FakeBoundary()
        self.assertEqual(boundary.classify(ValueError("x")).category, ErrorCategory.VALIDATION)


if __name__ == "__main__": unittest.main()
