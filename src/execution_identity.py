"""Identity model for multi-account, multi-instance OIA execution."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ExecutionIdentity:
    account_id: str
    instance_id: str
    environment_id: str
    session_id: str

    def __post_init__(self):
        for value, name in ((self.account_id, "account_id"), (self.instance_id, "instance_id"), (self.environment_id, "environment_id"), (self.session_id, "session_id")):
            if not value or not value.strip():
                raise ValueError(f"{name} is required")

    @property
    def key(self) -> str:
        return ":".join((self.account_id.strip(), self.instance_id.strip(), self.environment_id.strip(), self.session_id.strip()))

    def provenance(self) -> dict[str, str]:
        return {
            "account_id": self.account_id.strip(),
            "instance_id": self.instance_id.strip(),
            "environment_id": self.environment_id.strip(),
            "session_id": self.session_id.strip(),
            "identity_key": self.key,
        }

@dataclass(frozen=True)
class ExecutionIdentityContext:
    identity: ExecutionIdentity
    command_id: str
    execution_id: str

    def __post_init__(self):
        if not self.command_id.strip():
            raise ValueError("command_id is required")
        if not self.execution_id.strip():
            raise ValueError("execution_id is required")
