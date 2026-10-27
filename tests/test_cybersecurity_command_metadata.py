import unittest
from types import SimpleNamespace

from src.cybersecurity_command_metadata import (
    AuthenticatedCybersecurityCommandMetadata,
    build_authenticated_command_resolver,
)


class AuthenticatedCommandResolverTests(unittest.TestCase):
    def setUp(self):
        self.command = SimpleNamespace(
            id="cmd-123", source_action_kind="cybersecurity_remediation"
        )
        self.metadata = AuthenticatedCybersecurityCommandMetadata(
            command_id="cmd-123",
            case_id="case-456",
            registry_version=3,
            action="remediate",
            authentication_context_id="authctx-789",
        )

    def test_resolves_exact_authenticated_metadata(self):
        resolver = build_authenticated_command_resolver(lambda _command: self.metadata)
        self.assertEqual(resolver(self.command), ("case-456", 3, "remediate"))

    def test_rejects_command_id_mismatch(self):
        wrong = AuthenticatedCybersecurityCommandMetadata(
            command_id="other-command",
            case_id="case-456",
            registry_version=3,
            action="remediate",
            authentication_context_id="authctx-789",
        )
        resolver = build_authenticated_command_resolver(lambda _command: wrong)
        with self.assertRaisesRegex(ValueError, "command ID mismatch"):
            resolver(self.command)

    def test_rejects_wrong_metadata_type(self):
        resolver = build_authenticated_command_resolver(lambda _command: {
            "command_id": "cmd-123",
            "case_id": "case-456",
            "registry_version": 3,
            "action": "remediate",
            "authentication_context_id": "authctx-789",
        })
        with self.assertRaisesRegex(ValueError, "invalid metadata object"):
            resolver(self.command)

    def test_rejects_non_security_command(self):
        self.command.source_action_kind = "general"
        resolver = build_authenticated_command_resolver(lambda _command: self.metadata)
        with self.assertRaisesRegex(ValueError, "not classified"):
            resolver(self.command)

    def test_rejects_invalid_metadata_fields(self):
        with self.assertRaisesRegex(ValueError, "positive integer"):
            AuthenticatedCybersecurityCommandMetadata(
                command_id="cmd-123",
                case_id="case-456",
                registry_version=True,
                action="remediate",
                authentication_context_id="authctx-789",
            )
        with self.assertRaisesRegex(ValueError, "allowed cybersecurity action"):
            AuthenticatedCybersecurityCommandMetadata(
                command_id="cmd-123",
                case_id="case-456",
                registry_version=3,
                action="execute-shell",
                authentication_context_id="authctx-789",
            )


if __name__ == "__main__":
    unittest.main()
