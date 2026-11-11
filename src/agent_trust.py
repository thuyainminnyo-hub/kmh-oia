"""Deterministic agent identity, delegated authority, and action governance.

This module is a local reference implementation. It does not authenticate remote
workloads, issue cryptographic credentials, or replace a production IAM system.
Model-generated text and retrieved/tool content are never authorization inputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    owner_principal: str
    workload: str
    environment: str
    active: bool = True


@dataclass(frozen=True)
class DelegationGrant:
    grant_id: str
    issuer: str
    subject_agent_id: str
    scopes: frozenset[str]
    expires_at_epoch: int
    parent_grant_id: str | None = None


@dataclass(frozen=True)
class ActionRequest:
    request_id: str
    agent_id: str
    tool_name: str
    resource: str
    required_scope: str


@dataclass(frozen=True)
class HumanApproval:
    request_id: str
    agent_id: str
    tool_name: str
    resource: str
    approver: str
    approved: bool


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    request_id: str
    agent_id: str
    tool_name: str
    resource: str
    decision: str
    reason: str


class AuditSink(Protocol):
    @property
    def events(self) -> tuple[AuditEvent, ...]: ...

    def append(self, event: AuditEvent) -> None: ...


class InMemoryAppendOnlyAudit:
    """Deterministic local audit sink; production storage must enforce immutability."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def append(self, event: AuditEvent) -> None:
        if event.sequence != len(self._events) + 1:
            raise ValueError("audit sequence must be contiguous")
        self._events.append(event)


class AgentTrustRegistry:
    """Registry and deterministic policy enforcement for bounded agent actions."""

    def __init__(
        self,
        *,
        sensitive_tools: frozenset[str] = frozenset({"publish", "delete", "payment", "deploy"}),
        audit: AuditSink | None = None,
    ) -> None:
        self._agents: dict[str, AgentIdentity] = {}
        self._grants: dict[str, DelegationGrant] = {}
        self._sensitive_tools = sensitive_tools
        self.audit = audit or InMemoryAppendOnlyAudit()

    def register_agent(self, identity: AgentIdentity) -> None:
        if not all((identity.agent_id.strip(), identity.owner_principal.strip(),
                    identity.workload.strip(), identity.environment.strip())):
            raise ValueError("agent identity fields must be non-empty")
        if identity.agent_id in self._agents:
            raise ValueError("agent identity already registered")
        self._agents[identity.agent_id] = identity

    def revoke_agent(self, agent_id: str) -> None:
        identity = self._agents.get(agent_id)
        if identity is None:
            raise KeyError("unknown agent")
        self._agents[agent_id] = AgentIdentity(
            identity.agent_id, identity.owner_principal, identity.workload,
            identity.environment, active=False,
        )

    def add_root_grant(self, grant: DelegationGrant) -> None:
        if grant.parent_grant_id is not None:
            raise ValueError("root grant cannot have a parent")
        identity = self._agents.get(grant.subject_agent_id)
        if identity is None or grant.issuer != identity.owner_principal:
            raise ValueError("root grant issuer must match the agent owner")
        self._add_grant(grant)

    def delegate(self, grant: DelegationGrant) -> None:
        if grant.parent_grant_id is None:
            raise ValueError("delegated grant requires a parent grant")
        parent = self._grants.get(grant.parent_grant_id)
        if parent is None:
            raise ValueError("parent grant not found")
        if grant.issuer != parent.subject_agent_id:
            raise ValueError("delegation issuer must be the parent agent")
        if not grant.scopes or not grant.scopes.issubset(parent.scopes):
            raise ValueError("delegated scopes must be a non-empty subset of parent scopes")
        self._add_grant(grant)

    def _add_grant(self, grant: DelegationGrant) -> None:
        if not grant.grant_id.strip() or grant.grant_id in self._grants:
            raise ValueError("grant ID must be non-empty and unique")
        if grant.subject_agent_id not in self._agents:
            raise ValueError("grant subject agent is not registered")
        if not grant.scopes:
            raise ValueError("grant must contain at least one scope")
        self._grants[grant.grant_id] = grant

    def _effective_grant(self, agent_id: str, now_epoch: int) -> DelegationGrant | None:
        matches: list[DelegationGrant] = []

        def visit(
            grant: DelegationGrant,
            inherited_scopes: frozenset[str] | None,
            seen: frozenset[str],
        ) -> None:
            if grant.grant_id in seen or grant.expires_at_epoch <= now_epoch:
                return
            if inherited_scopes is not None and not grant.scopes.issubset(inherited_scopes):
                return
            subject = self._agents.get(grant.subject_agent_id)
            if subject is None or not subject.active:
                return
            if grant.subject_agent_id == agent_id:
                matches.append(grant)
                return
            next_seen = seen | {grant.grant_id}
            for child in self._grants.values():
                if (child.parent_grant_id == grant.grant_id
                        and child.issuer == grant.subject_agent_id):
                    visit(child, grant.scopes, next_seen)

        for root in self._grants.values():
            if root.parent_grant_id is None:
                visit(root, None, frozenset())
        # Multiple independent authority chains for one agent are ambiguous:
        # fail closed rather than merging privileges.
        return matches[0] if len(matches) == 1 else None

    def authorize(
        self,
        request: ActionRequest,
        *,
        now_epoch: int,
        approval: HumanApproval | None = None,
    ) -> AuthorizationDecision:
        identity = self._agents.get(request.agent_id)
        decision = AuthorizationDecision(False, "denied")
        if not all((request.request_id.strip(), request.tool_name.strip(),
                    request.resource.strip(), request.required_scope.strip())):
            decision = AuthorizationDecision(False, "request fields must be non-empty")
        elif identity is None or not identity.active:
            decision = AuthorizationDecision(False, "agent is unknown or revoked")
        else:
            grant = self._effective_grant(request.agent_id, now_epoch)
            if grant is None or request.required_scope not in grant.scopes:
                decision = AuthorizationDecision(False, "no valid delegated grant for required scope")
            elif request.tool_name in self._sensitive_tools and not self._approval_matches(request, approval):
                decision = AuthorizationDecision(False, "exact human approval required")
            else:
                decision = AuthorizationDecision(True, "authorized by deterministic policy")
        self.audit.append(AuditEvent(
            sequence=len(self.audit.events) + 1,
            request_id=request.request_id,
            agent_id=request.agent_id,
            tool_name=request.tool_name,
            resource=request.resource,
            decision="allow" if decision.allowed else "deny",
            reason=decision.reason,
        ))
        return decision

    @staticmethod
    def _approval_matches(
        request: ActionRequest, approval: HumanApproval | None
    ) -> bool:
        return bool(
            approval is not None
            and approval.approved
            and approval.request_id == request.request_id
            and approval.agent_id == request.agent_id
            and approval.tool_name == request.tool_name
            and approval.resource == request.resource
            and approval.approver.strip()
        )
