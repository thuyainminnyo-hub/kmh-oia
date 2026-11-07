"""Fail-closed identity and delegated-authorization contracts.

This module is a pure, deterministic policy decision point. It does not
authenticate credentials, verify cryptographic signatures, persist revocation,
or execute tools. Callers must supply identity data from a separately trusted
authentication boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Iterable


@dataclass(frozen=True)
class PrincipalIdentity:
    """Authenticated principal established by an upstream trusted verifier."""

    subject: str
    tenant_id: str
    issuer: str
    authenticated: bool
    active: bool
    authentication_method: str


@dataclass(frozen=True)
class AgentIdentity:
    """Identity of the agent requesting an action."""

    subject: str
    issuer: str
    active: bool


@dataclass(frozen=True)
class DelegationGrant:
    """A bounded delegation assertion; signature verification is out of scope."""

    delegation_id: str
    issuer_subject: str
    subject: str
    tenant_id: str
    audience: str
    scopes: tuple[str, ...]
    not_before: datetime
    expires_at: datetime
    revoked: bool = False


@dataclass(frozen=True)
class AuthorizationRequest:
    """Immutable authorization input, bound to one request and one tool."""

    request_id: str
    principal: PrincipalIdentity
    actor: AgentIdentity
    tenant_id: str
    action: str
    resource: str
    tool_name: str
    policy_version: str
    delegation: DelegationGrant | None = None
    approval_reference: str | None = None


@dataclass(frozen=True)
class PolicyRule:
    """Exact-match rule; wildcards are intentionally unsupported in V1."""

    action: str
    resource: str
    tool_name: str
    requires_approval: bool = False


@dataclass(frozen=True)
class AuthorizationDecision:
    """Auditable PDP result. This is not itself a signed audit receipt."""

    allowed: bool
    reason_code: str
    policy_version: str
    request_digest: str
    evaluated_at: datetime


def _aware_utc(value: datetime) -> datetime | None:
    if value.tzinfo is None or value.utcoffset() is None:
        return None
    return value.astimezone(timezone.utc)


def _request_digest(request: AuthorizationRequest) -> str:
    delegation = request.delegation
    payload = {
        "request_id": request.request_id,
        "principal": {
            "subject": request.principal.subject,
            "tenant_id": request.principal.tenant_id,
            "issuer": request.principal.issuer,
            "authenticated": request.principal.authenticated,
            "active": request.principal.active,
            "authentication_method": request.principal.authentication_method,
        },
        "actor": {
            "subject": request.actor.subject,
            "issuer": request.actor.issuer,
            "active": request.actor.active,
        },
        "tenant_id": request.tenant_id,
        "action": request.action,
        "resource": request.resource,
        "tool_name": request.tool_name,
        "policy_version": request.policy_version,
        "approval_reference": request.approval_reference,
        "delegation": None if delegation is None else {
            "delegation_id": delegation.delegation_id,
            "issuer_subject": delegation.issuer_subject,
            "subject": delegation.subject,
            "tenant_id": delegation.tenant_id,
            "audience": delegation.audience,
            "scopes": sorted(delegation.scopes),
            "not_before": delegation.not_before.isoformat(),
            "expires_at": delegation.expires_at.isoformat(),
            "revoked": delegation.revoked,
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(canonical.encode("utf-8")).hexdigest()


class PolicyDecisionPoint:
    """Fail-closed PDP with exact-match rules and bounded delegation checks."""

    def __init__(self, policy_version: str, rules: Iterable[PolicyRule]) -> None:
        if not policy_version.strip():
            raise ValueError("policy_version must not be empty")
        self._policy_version = policy_version
        self._rules = tuple(rules)

    def evaluate(
        self, request: AuthorizationRequest, *, now: datetime
    ) -> AuthorizationDecision:
        evaluated_at = _aware_utc(now)
        digest = _request_digest(request)

        def deny(reason: str) -> AuthorizationDecision:
            return AuthorizationDecision(
                False, reason, self._policy_version, digest,
                evaluated_at or now,
            )

        if evaluated_at is None:
            return deny("INVALID_EVALUATION_TIME")
        if request.policy_version != self._policy_version:
            return deny("POLICY_VERSION_MISMATCH")
        if not all((
            request.request_id.strip(),
            request.tenant_id.strip(),
            request.action.strip(),
            request.resource.strip(),
            request.tool_name.strip(),
        )):
            return deny("MISSING_REQUEST_CONTEXT")

        principal = request.principal
        actor = request.actor
        if not principal.authenticated or not principal.active:
            return deny("PRINCIPAL_NOT_AUTHENTICATED_OR_INACTIVE")
        if not all((principal.subject.strip(), principal.tenant_id.strip(), principal.issuer.strip(),
                    principal.authentication_method.strip())):
            return deny("INCOMPLETE_PRINCIPAL_IDENTITY")
        if not actor.active or not actor.subject.strip() or not actor.issuer.strip():
            return deny("AGENT_IDENTITY_INACTIVE_OR_INCOMPLETE")
        if request.tenant_id != principal.tenant_id:
            return deny("TENANT_MISMATCH")

        matching = [
            rule for rule in self._rules
            if (rule.action, rule.resource, rule.tool_name)
            == (request.action, request.resource, request.tool_name)
        ]
        if len(matching) != 1:
            return deny("NO_UNIQUE_POLICY_RULE")
        rule = matching[0]

        grant = request.delegation
        if grant is None:
            if actor.subject != principal.subject or actor.issuer != principal.issuer:
                return deny("DELEGATION_REQUIRED")
        else:
            not_before = _aware_utc(grant.not_before)
            expires_at = _aware_utc(grant.expires_at)
            if not_before is None or expires_at is None or expires_at <= not_before:
                return deny("INVALID_DELEGATION_TIME")
            if grant.revoked:
                return deny("DELEGATION_REVOKED")
            if grant.issuer_subject != principal.subject or grant.subject != actor.subject:
                return deny("DELEGATION_SUBJECT_MISMATCH")
            if grant.tenant_id != request.tenant_id:
                return deny("DELEGATION_TENANT_MISMATCH")
            if grant.audience != request.tool_name:
                return deny("DELEGATION_AUDIENCE_MISMATCH")
            if evaluated_at < not_before or evaluated_at >= expires_at:
                return deny("DELEGATION_OUTSIDE_VALIDITY_WINDOW")
            required_scope = f"{request.action}:{request.resource}"
            if required_scope not in grant.scopes:
                return deny("DELEGATION_SCOPE_MISSING")

        if rule.requires_approval and not (request.approval_reference or "").strip():
            return deny("HUMAN_APPROVAL_REQUIRED")

        return AuthorizationDecision(
            True, "ALLOW", self._policy_version, digest, evaluated_at
        )
