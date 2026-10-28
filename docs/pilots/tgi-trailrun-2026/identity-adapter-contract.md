# TGiTrailRun Runner Safety Pilot — Trusted Identity Adapter Contract

**Status:** DESIGN CONTRACT ONLY — authentication is not implemented by this document.
**Release decision:** HOLD / NOT VERIFIED.
**Data mode:** synthetic fixtures only; no live runner, medical, or location data.

## 1. Purpose

Define the minimum trusted identity boundary required before exposing `TrailRunIncidentService` through a network or operator-facing adapter. The current service accepts caller-supplied `role` strings and a constructor-supplied checkpoint allowlist. Those values are policy inputs, not proof of identity. A request body, query parameter, header copied without verification, or a freely constructed Python object must not be treated as trusted identity.

This contract does not select an identity provider, API framework, credential format, or deployment model. Those choices must be recorded before implementation.

## 2. Trust boundary

The intended path is:

`Untrusted HTTP / operator request → Credential verifier → Server-side identity-to-role/scope mapping → Trusted request context → Authorization policy → Incident service → Storage`

Only the credential-verification adapter may establish authentication. Only server-controlled mapping may assign pilot roles and checkpoint scope. The service and storage must not accept authorization claims from user-controlled incident payload fields.

The pilot must not instantiate an arbitrary `VerifiedPrincipal` or similarly named value from request data and claim that this authenticates the caller. A value object's name or constructor is not a security boundary.

## 3. Provider-agnostic adapter contract

The selected adapter must provide equivalent behavior to the following logical operations. These are requirements, not a claim that the named API already exists.

### Authentication

- Accept a request credential through the selected framework's supported authentication mechanism.
- Validate it using the configured provider's documented verification process.
- Reject missing, malformed, expired, not-yet-valid, wrong-issuer, wrong-audience, revoked, or otherwise invalid credentials as applicable to the selected protocol.
- Fail closed on provider unavailability, configuration errors, unsupported algorithms, key-rotation failures, or incomplete verification.
- Do not log credential material, raw tokens, session cookies, or secrets.
- Avoid treating an unverified decoded token/payload as authenticated claims.

### Server-side identity mapping

After successful credential verification only:

- Extract a stable provider subject identifier and issuer/tenant context required for audit and tenant isolation.
- Map the authenticated identity or approved groups to the pilot role using server-side configuration/allowlists. Do not trust a client-supplied `role` or `reported_by_role` as the source of authority.
- Resolve allowed checkpoint IDs from server-side assignments or an approved authorization source. Do not accept arbitrary checkpoint IDs from query/body parameters as the caller's scope.
- Deny by default when the identity, role mapping, checkpoint mapping, or tenant context is absent, ambiguous, stale, or invalid.
- Define how role revocation and checkpoint assignment changes become effective; do not cache authorization longer than the approved revocation model permits.

### Request context and service boundary

- Create the trusted request context only after authentication and mapping succeed.
- Bind the context to the authenticated subject, issuer/tenant (when applicable), mapped role, and explicitly resolved checkpoint scope.
- Make the authenticated subject and authorization context immutable for the lifetime of one request.
- Ensure network handlers derive all authorization inputs from that context; ignore/reject user-supplied values that attempt to override identity, role, subject, tenant, or allowed checkpoint IDs.
- Keep the raw storage adapter private to the application/service layer. Network handlers must not expose direct store methods.
- Re-check incident checkpoint scope for read, transition, and audit access; fail closed when stored scope metadata is missing or malformed.
- Keep state changes and audit writes atomic. A denied request must not mutate incident state, event receipts, or audit records.

### Audit attribution

- Record a stable, verified actor subject identifier and issuer/tenant reference (or an approved privacy-preserving stable identifier), not only a free-form role label.
- Record the server-mapped role, action, target incident, timestamp, result/reason code, correlation ID, and policy/mapping version when available.
- Never record raw credentials. Define retention and access controls for audit records before any real operational data is accepted.
- Distinguish authentication failure, authorization denial, scope denial, policy/configuration error, and unexpected internal error in safe logs.

## 4. Required negative tests

The adapter/service integration is not acceptable until all applicable tests run against the chosen real framework and verifier, not only mocks:

1. No credential → rejected before service/storage access.
2. Invalid signature or provider validation failure → rejected.
3. Expired/not-yet-valid credential and issuer/audience/tenant mismatch → rejected where supported by the chosen protocol.
4. A request-body role such as `race_control` cannot elevate an authenticated volunteer.
5. A request-body or query checkpoint cannot expand the authenticated user's server-resolved checkpoint scope.
6. Unknown or unmapped identity/group → denied by default.
7. Removed role/checkpoint assignment → access denied according to the documented revocation policy.
8. An out-of-scope incident cannot be created, read, transitioned, or have its audit viewed.
9. Direct storage access is not reachable from the public API boundary.
10. Unauthorized attempts leave incident status, event receipt, and audit count unchanged.
11. Audit entries refer to the verified actor subject and server-mapped role; caller-provided actor fields cannot spoof attribution.
12. Invalid incident schema is rejected before persistence, including any future new API entry path.
13. Authentication provider or configuration failure fails closed and produces no partial state mutation.

Use synthetic identities and fixtures only. Include both positive role-mapping tests and negative privilege-escalation tests.

## 5. Decisions required before implementation

The project owner/security reviewer must record:

- API framework and deployment entry point.
- Identity provider/protocol and authoritative issuer/tenant configuration.
- Supported credential type and revocation/session invalidation behavior.
- Authoritative source for user/group-to-role mapping.
- Authoritative source for checkpoint-scope mapping and scope-change latency.
- Stable audit actor identifier, retention, and access policy.
- Final role/action matrix approved by the race director and medical lead.
- Named security/privacy reviewers and acceptance evidence location.

Do not add a fake verifier, hard-coded demonstration token, self-asserted principal factory, or unverified token decoder as a substitute for these decisions.

## 6. Exit criteria

The authentication gate can move from **DESIGN** to **IMPLEMENTED** only when the selected verifier is integrated at the actual application entry point, the role/scope mapping is server-controlled, and all applicable negative tests exist.

It can move to **VERIFIED** only when the exact commit's CI passes, the integration tests exercise the real verification boundary in a controlled test environment, the audit attribution is inspected, and independent security/privacy plus race-director/medical-lead approvals are recorded.

This document alone does not satisfy either gate.

## 7. Current evidence and next action

- Exact known branch head at the time of this review: `80a667628690cca4d90a7c1399494c499cdfa51c`.
- CI on that commit: [KMH OIA Tests #1061](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40624234724) and [KMH OIA Validation #980](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40624234756) completed successfully.
- PR #137 is open and draft; it is not merged.
- Authentication, trusted actor derivation, role/scope mapping, owner approvals, and production verification remain open.

Next action: choose and document the actual application entry point and identity provider, then implement the adapter at that boundary with tests. Until then, keep the pilot synthetic-only and release HOLD.
