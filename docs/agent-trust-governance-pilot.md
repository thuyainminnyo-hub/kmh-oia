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
- Added an optional SQLite-backed durable audit sink with a SHA-256 hash chain, append-only update/delete triggers, restart persistence, and chain verification (`src/durable_audit.py`).
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

### SCITT interoperability research and SCRAPI client boundary (2026-11-12)

RFC 9943 (June 2026) is the adopted IETF Standards Track architecture for signed-statement transparency. It defines COSE-based Signed Statements, Transparency Services, Registration Policies and independently verifiable Receipts. It explicitly allows one Signed Statement to be registered with multiple independent Transparency Services; relying parties decide which issuers and services to trust. A Receipt proves registration/inclusion, not the truth of the issuer's claims.

The SCITT Reference APIs draft-ietf-scitt-scrapi-11 (June 26, 2026) was approved by the IESG as Proposed Standard on June 29, 2026 and is in the RFC Editor queue; it is not yet an RFC. Its mandatory client operations are key discovery at /.well-known/scitt-keys, POST /entries for Signed Statement registration, and receipt resolution at the returned Location. Registration can return 201 with an immediate COSE receipt or 202 with a Location for later resolution; receipt resolution can return 200, 204 while pending, or 404. Clients must handle generic HTTP status classes and Concise Problem Details rather than hard-coding only illustrative statuses. Key retention is important: old TS verification keys must remain available for as long as old receipts need verification.

Added src/scitt_client.py as an injectable-transport protocol boundary:
- SCRAPI key discovery request with application/cbor.
- Signed Statement registration with application/cose and explicit 201/202 result handling.
- Receipt resolution with explicit ready/pending/not-found outcomes.
- HTTPS-only service origin and same-origin Location enforcement to prevent credential or receipt polling redirects to arbitrary hosts.
- No implicit polling, retry, signing, CBOR decoding, COSE verification or real network transport; these are intentionally separate adapters/gates.

Added tests/test_scitt_client.py for key discovery, immediate registration, asynchronous registration and resolution, not-found handling, cross-origin/downgrade rejection, media-type validation and invalid async bodies.

Agent-specific profiles remain drafts. The SCITT WG list currently includes draft-thaha-scitt-agent-execution-evidence-02, draft-emirdag-scitt-ai-agent-execution-01 and draft-mih-scitt-agent-action-capsule-03. The Action Capsule draft makes an important distinction between an action being permitted and what actually happened, and distinguishes dispatch from observed/bound effect. These are design inputs, not adopted standards. KMH should keep its application-specific Agent Action Evidence schema separate from the base SCRAPI transport layer.

### CCF COSE receipt profile review and verifier boundary (2026-11-12)

The latest Datatracker revision is draft-ietf-scitt-receipts-ccf-profile-06, published 2026-10-22 and still an active Internet-Draft (not an RFC). Its history records the COSE Verifiable Data Structure Algorithms IANA registration as approved on 2026-11-10. The CCF profile defines inclusion and consistency proofs for append-only CCF ledgers. For inclusion verification, the verifier recomputes SHA-256 over the candidate Signed Statement bytes, requires every proof leaf data-hash to equal that locally computed digest, validates the proof schema, computes the Merkle root, and verifies the detached COSE receipt signature over that root using a trusted CCF/Transparency Service key. Multiple proofs in one receipt must agree on the root. Consistency verification additionally requires a previously trusted older root and checks that the proof extends that state.

Added src/receipt_verification.py as a strict orchestration boundary:
- Recomputes candidate Signed Statement SHA-256 locally (does not trust a digest in the receipt).
- Requires detached payload and SCITT VDP header/inclusion proof label.
- Delegates CBOR decoding, CCF proof schema validation, Merkle-root calculation and COSE signature/key/service-identity verification to injected adapters.
- Requires all inclusion proofs to bind the candidate statement and agree on one root.
- Returns a VerifiedInclusion result only after the injected cryptographic verifier accepts the receipt.

Added tests/test_receipt_verification.py for valid inclusion binding, wrong statement digest, inconsistent proof roots, invalid COSE/service identity, embedded payload, missing proofs and missing trusted keys. Tests use fake adapters and do NOT prove cryptographic conformance.

Not implemented: actual CBOR/COSE codec, CCF proof schema implementation, Merkle hash algorithm implementation, key discovery-to-trust policy, COSE signature verification, certificate chain/rotation/revocation, consistency proof verifier, checkpoint/epoch trust, multi-TS quorum/policy, live service integration or offline bundle verification. This is a security-critical adapter boundary, not a production verifier. Use official CCF verifier implementations/conformance vectors or a reviewed library before enabling trust decisions.

## Current limitations — do not overstate readiness
- Registry and grants are in-memory only; restart loses state.
- Agent IDs are application identifiers, not cryptographically authenticated workload identities.
- Grants are persistent in-memory policy records, not zero-standing-privilege JIT credentials.
- Grants are not signed and there is no credential issuance/rotation integration.
- HumanApproval is a local data contract, not a verified human authentication workflow.
- The default audit sink is still in-memory. The optional SQLite sink persists events and detects row tampering through a hash chain, but a privileged database administrator can still rewrite the database and recompute the chain; it is not independently administered, WORM storage, or externally anchored.
- The local trust gate is wired into OIARuntime/GovernedTool immediately before the existing tool allowlist and executor. Per-tool scopes must be configured explicitly; absent mappings fail closed.
- No MCP server, A2A transport, external policy engine, or production secrets integration is included.
- Prompt injection is mitigated at the authorization boundary by refusing to treat text as authority; this is not a model-level prompt-injection detector.
- No production deployment, CI run, or external penetration test is claimed.

## Standards and implementation research (2026-11-12)

NIST's October 27, 2026 *Design Tenets for Agent Identity Management Systems* provides the primary architecture checklist for this pilot. It calls for distinct cryptographically verifiable agent identity, cryptographic linkage and attenuated delegation, zero standing privilege, short-lived audience-specific JIT authorization with runtime re-verification, risk-triggered human review, signed task mandates, separation of policy from reasoning, deterministic access decisions, and independent tamper-evident evidence. This pilot is only a local policy prototype; it does not yet demonstrate conformance.

### November 2026 mandate-protocol research

The IETF draft *Verifiable Mandates for Agents Acting Across Administrative Domains* (draft-hulea-wimse-agent-mandate-01, published 2026-11-01) distinguishes evidence that a delegator has authority from evidence that the delegator actually granted a mandate. It also separates deterministic mandate validation from the relying party's own authorization decision, attributes claims to their issuers, and requires mandate constraints to remain enforced after token exchange. This is an active Internet-Draft, not an adopted RFC.

The IETF draft *Credential Delegation Protocol for AI Agents in Multi-System Environments* (draft-sweeney-wimse-credential-delegation-02, published 2026-10-30) profiles OAuth Token Exchange, DPoP, Rich Authorization Requests and CIBA, with ephemeral agent keys, resource-scoped capability tokens, server-side credential vaulting, consent, cascading revocation and audit. It is also work in progress, not a standard.

These drafts reinforce that a signed mandate alone is not sufficient: the relying party must separately trust the issuer and the source of the delegator's authority; validate the mandate; then apply its own authorization policy. Prompt injection can still manipulate an agent into requesting an action that is technically within its mandate, so runtime risk controls and human intent checks remain necessary.

### IETF draft review: authority is distinct from mandate

The current IETF Datatracker entry confirms `draft-hulea-wimse-agent-mandate-01` is an active individual Internet-Draft last updated 2026-11-01, not an endorsed IETF standard or RFC. Its central design distinction is important for KMH: (1) an Authority Assertion says what powers a delegator holds for a principal; (2) a separate Mandate Assertion says what authority was actually granted to the agent. A narrowing delegation chain alone cannot prove that the root delegator was entitled to delegate.

The draft also defines an explicit Validation Profile, attributed claims by artifact issuer/role, deterministic validation separate from relying-party policy, post-token-exchange constraint enforcement, status/revocation handling, obligations, and a single-execution access token. A valid mandate does not prove that the action reflects the principal's current intent or that the agent was not prompt-injected.

The October 30, 2026 WIMSE Credential Delegation Protocol draft profiles existing OAuth Token Exchange, DPoP, Rich Authorization Requests and CIBA rather than defining a new OAuth grant or token format. It proposes ephemeral agent keys, capability-shaped resource/operation tokens, credential wrapping, consent-gated delegation, cascading revocation and tamper-evident audit. Both documents are work in progress and must be treated as design input, not normative standards.

### Follow-up code refinement: separate authority evidence

Extended `src/mandates.py` so a root mandate issued by a third-party representative must reference a separately validated `AuthorityAssertion`. The assertion binds its issuer, principal, delegator, scopes, resources, expiry, nonce and key ID. Its verifier call is role-aware (`authority_source`) and mandate signature verification is role-aware (`mandate_issuer`), so the configured trust adapter can distinguish issuer roles. Child mandates preserve the original principal and must be issued by the parent agent identity. Tests cover missing authority evidence and scope/resource widening.

Important limitation: the role-aware `SignatureVerifier` is still only an interface. The test verifier is a digest fixture, not asymmetric cryptography. `VerifiedAuthorityAssertion` and `VerifiedMandate` are ordinary Python objects, not language-enforced unforgeable capabilities; only trusted in-process code may construct/pass them. Production must use a trusted key resolver that binds issuer + role + key ID to approved trust anchors, verify the delegator's instruction to the mandate issuer, and protect proof objects across process boundaries.

### November 2026 research: credential-to-execution evidence binding

The IETF Datatracker lists draft-thaha-wimse-agent-evidence-binding-03, last updated 2026-11-01, as an active individual Internet-Draft with no formal standing in the IETF standards process. It is a companion to the WIMSE AI Identity Management System draft and maps credential-level agent identity/policy claims to per-call execution evidence.

The draft separates two bindings:
- aee_evidence is a credential-level claim binding the expected Evidence Service, policy-pack digest and persistent logical agent ID, with optional assurance/registration/credential digests. It applies across the calls covered by that credential.
- AEE-Caller-Ref is a per-call HTTP Structured Field linking one caller execution receipt (evidence service, sequence, record hash, transaction and optional call digest) to the serving party's admission record. It must not be placed in a reusable multi-call token.

A serving party must validate credential and proof-of-possession, check registration and assurance freshness/status, authorize the principal and current actor, recompute the request digest itself (never trust the caller-provided digest), reject mismatches and replayed caller references, record an admission receipt for both allow and deny, and fail closed when required evidence cannot be checked. The draft explicitly says the Actor Chain is attribution, not proof of authority; authority across hops still needs per-hop signed evidence. The companion SCITT Agent Execution Evidence draft describes receipts, assurance statements and linked verification. Neither draft is an adopted RFC.

### SCITT Agent Execution Evidence profile review (2026-11-12)

The current IETF Datatracker entry identifies draft-thaha-scitt-agent-execution-evidence-02, last updated 2026-11-01, as an active individual Internet-Draft, intended Standards Track but with no RFC stream or formal standing. It profiles SCITT Signed Statements and transparency receipts for agent execution evidence. Its key architectural contribution is dual-sided evidence: the caller's Harness records why/how it made a call; the Serving Party records its independent admission decision and what it checked. Comparing both parties' hash-chained records can reveal an omitted call. It also specifies task lifecycle receipts, per-call model/tool decision points, policy/configuration digests on receipts, cross-operator call linking, registration policy, offline verification and Bundles.

The draft's explicit limits matter: only calls passing instrumented Decision Points are evidenced; activity inside an uninstrumented model/tool or through an unmediated channel is not captured. A hash chain alone is not a non-equivocating transparency service; epoch sealing, SCITT registration/receipts and independently verifiable log consistency are required. The draft is work in progress, not an adopted RFC.

### Local hash-chained receipt sequence refinement

Extended src/execution_evidence.py with an in-memory ExecutionEvidenceChain. It assigns/verifies contiguous receipt sequence order, binds each receipt to the preceding receipt digest, rejects sequence gaps and detects mutation during local chain verification. Added tests for successful chain verification, sequence-gap rejection and receipt-tampering detection.

This improves the local evidence prototype but is not a SCITT implementation: no COSE-signed statements, SCITT Registration API, transparency service, inclusion/consistency proofs, epoch statements, offline Bundle verifier, caller/serving-party dual chains, task lifecycle semantics, or remote storage/independent verification. The in-memory chain can be rewritten by the process owner and must not be represented as tamper-proof or independently auditable.

### Persistent serving-party evidence ledger

Added SQLiteServingEvidenceLedger to src/linked_evidence.py. It persists serving admission receipts across process restarts, computes the serving-side request digest, stores the receipt chain in a SQLite transaction, enforces a unique (serving party, caller agent, caller receipt digest) replay key at the database level, and verifies sequence continuity, predecessor links and receipt digests. SQLite append-only update/delete triggers are installed. Added tests for persistence/reopen, replay rejection after restart and append-only triggers.

Security boundary: SQLite transaction/unique constraints provide local atomicity and durable replay protection for this database. They do not provide cross-region/distributed replay protection across separate database instances, independent administration, WORM guarantees against a privileged database owner, signed receipts, remote transparency, or SCITT conformance. The caller evidence itself remains unauthenticated in this prototype. Deploy only behind an authenticated gateway until production cryptographic identity and receipt validation exist.

### Linked caller and serving-party evidence prototype

Added src/linked_evidence.py and tests/test_linked_evidence.py. The serving-side ledger independently recomputes the request digest, records allow/deny/indeterminate admission outcomes, rejects duplicate caller receipt references within this process, and chains admission receipts. A linking function checks request ID, caller identity, caller receipt digest and request digest across the caller and serving-party records. Tests cover successful linking, request substitution, duplicate-reference replay, identity/request mismatch and recording denied calls.

This is still an in-memory application prototype. It has no authenticated caller receipt signature, no independent trust registry, no persistent/distributed replay protection, no concurrency/transaction guarantees, no serving gateway integration, and no SCITT signed statement or transparency receipt. It cannot detect calls that bypass the instrumented gateway. Do not treat the hash chain as non-equivocating or tamper-proof against the process/database administrator.

### Local execution-evidence binding slice

Added src/execution_evidence.py and tests/test_execution_evidence.py:
- Credential-level evidence claim shape for evidence service, policy-pack digest, logical agent ID and optional assurance digest.
- Per-call receipt carrying logical/runtime agent IDs, policy digest, request digest, resource, tool, action, decision, reason code, timestamp and optional output digest.
- Request digest is computed by the local builder from canonicalized request content.
- Verification recomputes the digest from the actual received request and checks request ID, runtime identity, logical identity, policy digest and audit sequence.
- Tests cover successful link, request tampering, identity/policy/sequence mismatch, invalid claim digest and output digest.

This is a local prototype only: no signed JWT/CWT credential claim, no HTTP Structured Field parser/transport integration, no cryptographic Execution Receipt, no SCITT registration/transparency service, no remote linked verification, no atomic replay store, and no actual serving-party admission pipeline integration. The local digest receipt is not independently verifiable evidence of who executed an action; it becomes trustworthy only when authenticated workload identity, trusted signing, secure receipt storage and independent verification are implemented. The local AgentEvidenceClaim digest representation is a simplified prototype, not a wire-compatible implementation of the draft's digest structure.
### Local signed-mandate validation slice

Added `src/mandates.py` with:
- Canonical JSON serialization and SHA-256 payload digest for deterministic signature input.
- A pluggable `SignatureVerifier` interface; no production cryptographic algorithm or key is silently assumed.
- Audience, subject-agent, workload ID, time-window, maximum-lifetime, scope, resource and delegation-depth validation.
- Parent-child issuer linkage and attenuation checks for scopes, resources, expiry and delegation depth.
- A `VerifiedMandate` proof object returned only after validation; child validation requires this proof object rather than an arbitrary parent payload.
- Separate root `AuthorityAssertion` and `VerifiedAuthorityAssertion` flow for third-party delegators; the mandate and authority artifact signatures are checked with distinct issuer roles.
- Nonce replay detection through a pluggable `NonceStore`; the included in-memory implementation is single-process test/local only.

Added `tests/test_mandates.py` for signature tampering, wrong audience/identity, time bounds, lifetime, scope/resource escalation, root/child constraints, replay and depth limits. Its digest-only verifier is strictly a test fixture and is NOT a cryptographic signature implementation.

**Not implemented:** production Ed25519/JWS/KMS signing or verification, trusted issuer/key discovery and rotation, atomic distributed nonce storage, authenticated SPIFFE workload attestation, signed evidence of delegator authority, OAuth token exchange/DPoP/CIBA, mandate enforcement after downstream token exchange, production authorization policy, or runtime wiring of the mandate validator. The caller must obtain the parent `VerifiedMandate` from a trusted validator configured with an approved signature verifier and trust policy.

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
| Mandates | Local Authority Assertion + Mandate validation interfaces; no production crypto/runtime wiring | Trusted issuer-role anchors, proof of delegator instruction, Validation Profile, obligations and downstream enforcement |
| Policy/reasoning separation | Local deterministic gate | Prove untrusted model/tool text cannot mutate policy or credentials |
| Deterministic decision | Local rule checks | Versioned policy, resource/action decision tests |
| Immutable evidence | In-memory list only | Durable independent tamper-evident audit |
| Runtime monitoring | Basic request checks | Context/risk drift signals, revocation and containment evidence |

### Next implementation gates

1. Specify and threat-model the signed mandate schema and trust-root/key-rotation lifecycle; review the local validator against the IETF November 2026 mandate draft.
2. Add SPIFFE/SPIRE workload identity adapter behind a provider interface; retain a clearly labelled local test provider for unit tests only.
3. Implement task-scoped JIT authorization and per-invocation revocation/audience/resource checks.
4. Integrate a trusted out-of-band human approval provider and action-digest binding.
5. Implement durable independent audit with integrity verification, retention, and export.
6. Add production-crypto conformance tests for signature tampering, unknown/revoked issuer keys, wrong issuer/audience, expired/not-yet-valid mandate, distributed replay, delegation-chain tampering, confused deputy, cross-resource substitution, revoked workload, approval-key isolation, audit-store outage/fail-closed behavior, and historical verification after key rotation. The local mandate tests use a digest-only test verifier and do not prove cryptographic security. The SQLite sink has persistence, sequence, append-only trigger, and hash-chain tamper-detection tests.
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
