"""Resolver adapter contract for authenticated cybersecurity command metadata.

The provider is a trust boundary: it must obtain metadata from authenticated,
server-side command context, not user text or request-supplied dictionaries.
This adapter validates shape and command binding only; it does not authenticate
the provider, authorize a registry record, or execute remediation.
"""
from dataclasses import dataclass
from typing import Callable

from src.cybersecurity_executor_contract import EXECUTABLE_ACTIONS


@dataclass(frozen=True)
class AuthenticatedCybersecurityCommandMetadata:
    command_id: str
    case_id: str
    asset_id: str
    registry_version: int
    action: str
    authentication_context_id: str

    def __post_init__(self) -> None:
        for field_name in (
            "command_id", "case_id", "asset_id", "authentication_context_id"
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        if not isinstance(self.registry_version, int) or isinstance(self.registry_version, bool) or self.registry_version < 1:
            raise ValueError("registry_version must be a positive integer")
        if not isinstance(self.action, str) or not self.action.strip() or self.action not in EXECUTABLE_ACTIONS:
            raise ValueError("action is not an allowed cybersecurity action")


def build_authenticated_command_resolver(
    metadata_provider: Callable[[object], AuthenticatedCybersecurityCommandMetadata],
) -> Callable[[object], tuple[str, int, str, str]]:
    """Adapt trusted metadata to the registry guard's resolver signature.

    The provider must authenticate and bind metadata to the command server-side.
    The adapter rejects missing/wrongly typed metadata and command-ID mismatch.
    It intentionally does not treat a dataclass instance as proof of authenticity.
    """
    if not callable(metadata_provider):
        raise TypeError("metadata_provider must be callable")

    def resolve(command: object) -> tuple[str, int, str]:
        if getattr(command, "source_action_kind", None) != "cybersecurity_remediation":
            raise ValueError("command is not classified as cybersecurity remediation")
        metadata = metadata_provider(command)
        if not isinstance(metadata, AuthenticatedCybersecurityCommandMetadata):
            raise ValueError("trusted metadata provider returned an invalid metadata object")
        command_id = getattr(command, "id", None)
        if not isinstance(command_id, str) or metadata.command_id != command_id:
            raise ValueError("authenticated metadata command ID mismatch")
        return metadata.case_id, metadata.registry_version, metadata.action, metadata.asset_id

    return resolve
