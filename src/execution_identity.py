"""Canonical identity model for multi-account, multi-instance OIA execution."""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass

@dataclass(frozen=True)
class ExecutionIdentity:
    account_id: str
    instance_id: str
    environment_id: str
    session_id: str

    def __post_init__(self) -> None:
        for name in ("account_id", "instance_id", "environment_id", "session_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")

    def provenance(self) -> dict[str, str]:
        return {name: getattr(self, name).strip() for name in ("account_id", "instance_id", "environment_id", "session_id")}

    @property
    def key(self) -> str:
        canonical = json.dumps(self.provenance(), sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class ExecutionIdentityContext:
    identity: ExecutionIdentity
    command_id: str
    execution_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.identity, ExecutionIdentity):
            raise TypeError("identity must be an ExecutionIdentity")
        for name in ("command_id", "execution_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
