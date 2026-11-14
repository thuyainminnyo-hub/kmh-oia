"""Governed metadata registry for KMH OIA agents.

This registry is an in-process catalogue, not an authentication provider,
credential store, or authorization engine. Invocation must still pass through
the runtime's security and autonomy boundaries.
"""
from dataclasses import dataclass, replace
from enum import Enum
import re


class AgentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEPRECATED = "DEPRECATED"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class AgentRecord:
    agent_id: str
    name: str
    role: str
    owner: str
    version: str
    capabilities: tuple[str, ...]
    status: AgentStatus = AgentStatus.ACTIVE
    description: str = ""

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*", self.agent_id):
            raise ValueError("agent_id must be a stable lowercase identifier")
        for value, field_name in (
            (self.name, "name"),
            (self.role, "role"),
            (self.owner, "owner"),
            (self.version, "version"),
        ):
            if not value or not value.strip():
                raise ValueError(f"{field_name} is required")
        if not self.capabilities:
            raise ValueError("at least one capability is required")
        normalized = tuple(item.strip() for item in self.capabilities)
        if any(not item for item in normalized):
            raise ValueError("capabilities must not contain empty values")
        if len(set(normalized)) != len(normalized):
            raise ValueError("capabilities must be unique")
        object.__setattr__(self, "capabilities", normalized)
        if not isinstance(self.status, AgentStatus):
            raise ValueError("status must be an AgentStatus value")


class AgentRegistry:
    """Small deterministic registry with explicit lifecycle transitions."""

    _TRANSITIONS = {
        AgentStatus.ACTIVE: {
            AgentStatus.SUSPENDED,
            AgentStatus.DEPRECATED,
            AgentStatus.REVOKED,
        },
        AgentStatus.SUSPENDED: {
            AgentStatus.ACTIVE,
            AgentStatus.DEPRECATED,
            AgentStatus.REVOKED,
        },
        AgentStatus.DEPRECATED: {AgentStatus.REVOKED},
        AgentStatus.REVOKED: set(),
    }

    def __init__(self) -> None:
        self._records: dict[str, AgentRecord] = {}

    def register(self, record: AgentRecord) -> AgentRecord:
        if not isinstance(record, AgentRecord):
            raise TypeError("record must be an AgentRecord")
        if record.agent_id in self._records:
            raise ValueError(f"agent already registered: {record.agent_id}")
        self._records[record.agent_id] = record
        return record

    def get(self, agent_id: str) -> AgentRecord:
        try:
            return self._records[agent_id]
        except KeyError as error:
            raise KeyError(f"unknown agent: {agent_id}") from error

    def list(self, status: AgentStatus | None = None) -> tuple[AgentRecord, ...]:
        records = self._records.values()
        if status is not None:
            records = (record for record in records if record.status == status)
        return tuple(sorted(records, key=lambda record: record.agent_id))

    def transition_status(
        self, agent_id: str, new_status: AgentStatus
    ) -> AgentRecord:
        current = self.get(agent_id)
        if not isinstance(new_status, AgentStatus):
            raise ValueError("new_status must be an AgentStatus value")
        if new_status == current.status:
            return current
        if new_status not in self._TRANSITIONS[current.status]:
            raise ValueError(
                f"invalid agent lifecycle transition: "
                f"{current.status.value} -> {new_status.value}"
            )
        updated = replace(current, status=new_status)
        self._records[agent_id] = updated
        return updated
