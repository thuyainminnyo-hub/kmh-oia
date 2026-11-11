# Agent Trust & Governance Pilot — Implementation Record

## Status
**Implemented on an isolated feature branch; local verification pending. Not production-ready.**

Branch: `feat/agent-trust-governance-pilot`

## Scope delivered
- Unique application-level agent IDs and owner/workload/environment metadata.
- Root grants bound to the registered owner principal.
- Delegated grants with deterministic scope attenuation.
- Expiry checks at authorization time.
- Revocation of registered agents.
- Action-specific human approval for configured sensitive tools.
- Append-only in-memory decision audit with contiguous sequence numbers.
- Unit tests for allow/deny, escalation, expiry, approval binding, revocation, and audit ordering.

## Security invariants
1. Model output, retrieved text, tool descriptions, and tool output are untrusted data; they never grant authority.
2. Authorization is deterministic and evaluated for each action request.
3. A child grant cannot contain scopes absent from its parent grant.
4. A downstream agent cannot inherit broader authority than the delegation chain.
5. Sensitive actions require approval bound to the exact request ID, agent, tool, and resource.
6. Unknown, revoked, expired, ambiguous, or insufficiently scoped identities are denied.
7. Denied and allowed decisions are both audited.

## Run tests
```bash
python -m unittest tests.test_agent_trust -v
python -m unittest discover -s tests -v
```

## Current limitations — do not overstate readiness
- Registry and grants are in-memory only; restart loses state.
- Agent IDs are application identifiers, not cryptographically authenticated workload identities.
- Grants are persistent in-memory policy records, not zero-standing-privilege JIT credentials.
- Grants are not signed and there is no credential issuance/rotation integration.
- HumanApproval is a local data contract, not a verified human authentication workflow.
- Audit is append-only within this process only; it is not tamper-evident, durable, or externally anchored.
- The local trust gate is wired into OIARuntime/GovernedTool immediately before the existing tool allowlist and executor. Per-tool scopes must be configured explicitly; absent mappings fail closed.
- No MCP server, A2A transport, external policy engine, or production secrets integration is included.
- Prompt injection is mitigated at the authorization boundary by refusing to treat text as authority; this is not a model-level prompt-injection detector.
- No production deployment, CI run, or external penetration test is claimed.

## Standards alignment and remaining gaps

The implementation is directionally aligned with NIST's October 27, 2026 agent identity design tenets for distinct agent identities, delegation and attenuation, human review triggers, and architectural separation of policy from reasoning. It is not yet conformant evidence for those tenets: identity is not cryptographically verifiable, mandates are not signed, grants are not just-in-time/zero-standing, and human approval is not independently authenticated.

## Next implementation gates
1. Add resource-level policy, signed task mandates, and signed/short-lived JIT delegation credentials.
2. Bind logical agent identity to authenticated workloads and environment-specific credentials.
3. Replace data-object human approvals with authenticated out-of-band approval for high-impact actions.
4. Implement durable, tamper-evident append-only audit and trace/provenance correlation.
5. Add negative tests for prompt-injected tool output, confused-deputy attempts, replay, branching delegation, and revocation during a workflow.
6. Run the complete test suite and CI on this branch.
7. Require security and operations owner review before any production deployment.

## Decision boundary
This implementation is a deterministic local trust-control slice. It does not authorize production use and must not be described as enterprise-grade IAM until the above gates are completed and independently verified.
