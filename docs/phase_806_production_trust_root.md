# Phase 806 — Production Trust Root Configuration Gate

Date: 2026-10-21

## Delivered
Added `src/production_artifact_trust.py` as a production-specific entry point. It requires `KMH_OIA_ENVIRONMENT=production`, a JSON map of trusted Ed25519 public keys, explicit issuer and subject allowlists, the expected full 40/64-character source revision, and positive attestation max-age and clock-skew bounds. Placeholder identities, wildcard allowlists, malformed/incorrect-length keys, missing configuration, and invalid release pins are rejected.

The production loader compares the signed attestation source revision with the deployment revision before artifact loading, then delegates to the byte-measuring signed loader. The application accepts no private signing keys; signing belongs in a separately controlled build/release system. Key revocation requires removing the key from the active trusted-key configuration under controlled change management.

## Verification added
- Valid ephemeral Ed25519 test key/configuration loads exact byte snapshots.
- Missing environment, missing key, malformed public key, placeholder signer, wildcard allowlist, invalid time policy, and invalid release revision fail closed.
- Wrong source revision and tampered bytes prevent either loader callback from running.
- Tests use ephemeral keys and do not establish that any production trust root has been provisioned.

## Production boundary
The config loader exists, but no real production public key, protected signing workflow, key rotation/revocation process, actual format-specific production loaders, or deployment-time environment values are configured here. The normal orchestrator still does not identify actual deployed artifact paths and invoke this entry point. Those remain release prerequisites.

**Decision: Production HOLD.**

PR: https://github.com/thuyainminnyo-hub/kmh-oia/pull/97


## Phase 807 follow-up

Added `src/production_runtime_assembly.py` to bind the production verified artifact bundle to `TrustedDecisionLearningService` and `GovernedDecisionOrchestrator`, requiring a concrete policy-runtime binder before an assembly is returned. Production artifact paths, format loaders, public keys, and the actual policy binder remain deployment-owned inputs.
