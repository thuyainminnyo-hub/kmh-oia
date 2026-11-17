# P0-E.2 — Asymmetric Trust Hardening

Status: FEATURE-BRANCH IMPLEMENTATION; exact-head CI and independent security review pending; NOT PRODUCTION READY.

## Delivered scope
- Ed25519 assertion signing and public-key verification.
- Key IDs, overlap rotation (old verification key remains valid until revoked), and explicit key revocation.
- Ed25519 signatures for checkpoint payloads.
- Private keys are caller-supplied; this code does not persist or provision private key material.
- Tests cover valid signatures, tampering, expiry, role enforcement, rotation, revocation and checkpoint integrity.

## Boundaries / not claimed
- This is a library primitive, not a connected enterprise identity provider.
- No KMS/HSM adapter, secure key loading, automated rotation controller, external identity proofing, remote object-lock/WORM retention, multi-host replay store, or production runtime-wide rollout is delivered.
- The existing P0-E HMAC interfaces remain unchanged; callers must explicitly integrate this authority before using Ed25519 in the QA audit path.
- Checkpoint signing helper does not itself write to remote immutable storage.
- CI tests are not live runtime or ComfyUI evidence.

## Required next gates
1. Wire an approved identity provider to assertion issuance and secure key custody.
2. Integrate Ed25519 verification into the actual QA audit sink behind a migration-safe interface.
3. Add a provider-specific Object Lock/WORM adapter and test retention/denial/restore behavior.
4. Define operational key rotation, revocation propagation, compromise and recovery drills.
5. Re-run full exact-head CI, obtain independent security review, capture live runtime evidence, then request Owner release approval.

Release decision: HOLD. No merge, deployment, production promotion or live execution is authorized.
