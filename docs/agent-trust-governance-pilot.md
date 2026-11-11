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

## Standards and implementation research (2026-11-12)

NIST's October 27, 2026 *Design Tenets for Agent Identity Management Systems* provides the primary architecture checklist for this pilot. It calls for distinct cryptographically verifiable agent identity, cryptographic linkage and attenuated delegation, zero standing privilege, short-lived audience-specific JIT authorization with runtime re-verification, risk-triggered human review, signed task mandates, separation of policy from reasoning, deterministic access decisions, and independent tamper-evident evidence. This pilot is only a local policy prototype; it does not yet demonstrate conformance.

### Recommended KMH target architecture

1. **Workload identity:** keep a stable logical KMH agent ID, but bind each running workload instance to an attested SPIFFE ID. Obtain short-lived SVIDs through the SPIFFE Workload API; do not store private keys or static bearer credentials in agent configuration. Prefer X.509-SVID plus mTLS for service-to-service calls where supported. Use JWT-SVID only where federation or an L7 boundary requires it, with strict issuer, audience, expiry, signature and key-ID validation.
2. **Credential exchange:** use workload identity federation to exchange a validated SPIFFE JWT-SVID for a short-lived, audience-bound downstream access token. OpenAI documents this exact SPIFFE JWT-SVID-to-short-lived-token pattern. Use OAuth 2.0 Token Exchange (RFC 8693) where the authorization server supports delegated subject/actor token exchange; use certificate-bound tokens/mTLS (RFC 8705) to reduce bearer-token replay exposure where supported.
3. **Signed task mandate:** define a canonical, versioned mandate payload containing mandate ID, issuer/subject/actor identities, parent mandate, task ID, permitted tools/actions/resources, denied actions, maximum delegation depth, audience, issued-at, not-before, expiry, nonce, and policy version. Sign the canonical payload with an asymmetric issuer key held outside the agent process. Verify signature, issuer trust, audience, time window, nonce/replay state, and every parent-child scope intersection before issuing authority. Never accept a model-generated claim as a signature or authority source.
4. **Zero-standing/JIT grants:** keep agents with no active tool grant while idle. At task start, mint a narrowly scoped, short-lived capability for one task and audience. Re-authorize each tool invocation against current mandate, resource, risk and revocation state. Enforce separation of duties for conflicting actions; do not turn a JIT grant into a reusable long-lived credential.
5. **Human approval:** keep the existing exact action binding (request, agent, tool, resource), but move approval to a trusted out-of-band channel with a fresh human authentication step. Approval must be single-use, expire quickly, and be invalidated by any change to the action digest. The agent runtime must not be able to access or invoke the human signing key. Apply risk thresholds rather than asking for approval on every low-risk action to reduce consent fatigue.
6. **Independent evidence:** replace process-local audit with a durable append-only store outside the agent's administrative control. Record signed mandate digest, verified workload identity and credential thumbprint, delegation chain, policy version, request/action digest, approval evidence reference, allow/deny result, reason code, timestamps, revocation state and output/artifact digest. Add hash chaining or signed checkpoints, protected retention, external timestamping/anchoring, and independent read/verification. Preserve denied attempts and revocation receipts. Evidence must remain verifiable after credential rotation or agent retirement.
7. **Artifact provenance:** bind produced files, messages, code and their exact versions to the producing workload identity, mandate and execution trace using content digests; an agent ID string in metadata alone is not proof of provenance.

### Standards mapping and current gap

| Design area | Pilot status | Required evidence |
|---|---|---|
| Distinct identity | Application ID only | SPIFFE attestation and credential validation |
| Delegation | Local scope attenuation | Signed parent-linked mandate chain |
| Zero standing privilege | Not implemented | No idle grant; task-scoped JIT issuance |
| Short-lived authorization | Grant expiry only | Audience-bound ephemeral credential and per-call recheck |
| Human review | Local approval data object | Out-of-band authenticated, single-use approval |
| Mandates | Not implemented | Signature verification and constraint enforcement |
| Policy/reasoning separation | Local deterministic gate | Prove untrusted model/tool text cannot mutate policy or credentials |
| Deterministic decision | Local rule checks | Versioned policy, resource/action decision tests |
| Immutable evidence | In-memory list only | Durable independent tamper-evident audit |
| Runtime monitoring | Basic request checks | Context/risk drift signals, revocation and containment evidence |

### Next implementation gates

1. Specify and threat-model the signed mandate schema and trust-root/key-rotation lifecycle.
2. Add SPIFFE/SPIRE workload identity adapter behind a provider interface; retain a clearly labelled local test provider for unit tests only.
3. Implement task-scoped JIT authorization and per-invocation revocation/audience/resource checks.
4. Integrate a trusted out-of-band human approval provider and action-digest binding.
5. Implement durable independent audit with integrity verification, retention, and export.
6. Add tests for signature tampering, wrong issuer/audience, expired/not-yet-valid mandate, replay, delegation-chain tampering, confused deputy, cross-resource substitution, revoked workload, approval-key isolation, audit-store outage/fail-closed behavior, and historical verification after key rotation.
7. Run full CI against the exact current branch head; require security and operations owner review before any production deployment.

### Research references

- NIST, *Design Tenets for Agent Identity Management Systems* (2026-10-27): https://www.nist.gov/blogs/cybersecurity-insights/design-tenets-agent-identity-management-systems
- SPIFFE Workload API: https://spiffe.io/docs/latest/spiffe-specs/spiffe_workload_api/
- SPIRE Concepts and workload attestation: https://spiffe.io/docs/latest/spire-about/spire-concepts/
- OpenAI, *Configuring workload identity federation for SPIFFE*: https://developers.openai.com/api/docs/guides/workload-identity-federation/spiffe
- IETF RFC 8693, OAuth 2.0 Token Exchange: https://www.rfc-editor.org/rfc/rfc8693.html
- IETF RFC 8705, OAuth 2.0 Mutual-TLS Client Authentication and Certificate-Bound Access Tokens: https://www.rfc-editor.org/rfc/rfc8705.html

## Decision boundary
This implementation is a deterministic local trust-control slice. It does not authorize production use and must not be described as enterprise-grade IAM until the above gates are completed and independently verified.
