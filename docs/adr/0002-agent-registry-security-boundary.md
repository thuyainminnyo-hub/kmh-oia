# ADR 0002 — Agent Registry Security Boundary

- Status: Accepted for the first registry increment
- Date: 2026-11-14

## Decision

The initial AgentRegistry is an in-memory metadata catalogue only. It validates stable identity, owner, role, version, declared capabilities, and lifecycle status. It does not authenticate an agent and does not authorize tool invocation.

All actual tool calls remain subject to the existing runtime authorization and autonomy controls. Capability strings are descriptive metadata until a separate, tested policy enforcement increment binds a verified execution identity to a task-scoped grant.

## Rationale

Separating discovery metadata from authorization prevents a registry record from becoming a self-issued permission grant. Authorization must be enforced at the trusted execution boundary, deny by default, and checked for each request. High-risk external actions need explicit approval.

## Consequences

- Registry lookup cannot grant access.
- Agent-supplied identity or capability claims are not trusted authorization facts.
- Later integration must bind verified caller identity, task, tool, operation, and target resource.
- Suspended, deprecated, and revoked lifecycle states must be rejected at invocation time.
- Runtime audit records must include the effective authorization decision.

## References

- OWASP Authorization Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- OWASP AI Agent and MCP Security: https://github.com/OWASP/DevSecOpsGuideline/blob/master/current-version/2-Process/2-2-Develop/2-2-5-AI-Agent-and-MCP-Security.md
