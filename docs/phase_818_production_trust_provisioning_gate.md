# Phase 818 — Production Trust Provisioning & End-to-End Release Evidence Gate

Date: 2026-10-22

## Exact-head evidence

- Verified head: `4f4aaf7aa2545b561ef4d25ff6afd7f73903637a`.
- [KMH OIA Tests #795 — SUCCESS](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/39710956211).
- [KMH OIA Validation #713 — SUCCESS](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/39710956261).
- Current PR #97 is OPEN / DRAFT / UNMERGED. Reviews = 0; review threads = 0.

## Verified implementation

- `ProductionEvidenceRuntimeConfig.require_signed_release_bundle` defaults to `True`.
- Startup rejects missing signed release metadata before replay-store and execution-bridge construction.
- When bundle metadata is provided, the runtime factory invokes the consumer release gate before constructing the bridge.
- Full CI verifies repository tests and evidence-generation checks only. It does not prove that external signing credentials or production GitHub Environment rules are configured.

## Remaining externally grounded release gates

1. Provision the Ed25519 signing private key only as a protected signing Environment secret; separately provision matching raw public key bytes/key ID, exact issuer and subject allowlists in the runtime verifier configuration.
2. Configure and independently verify required reviewers on GitHub Environment `production-attestation`; confirm only approved main-branch workflow_dispatch runs may access the signer secret.
3. Run the trusted producer on a real approved main commit; capture run ID, full source SHA, artifact ID/name and GitHub artifact digest from GitHub's API rather than copying self-asserted metadata.
4. Complete the manual signing flow and verify the generated attestation using the separately provisioned public trust root.
5. Exercise a staging deployment/startup using the verified bundle; collect target runtime identity, health checks, provider-authenticity evidence and rollback/recovery evidence.
6. Obtain independent human review of PR #97 and the deployment/evidence pack before any production approval.

## Release decision

These are a checklist of remaining gates, not evidence that they have been executed. Do not generate substitute secrets, relax signature checks, or claim production readiness without direct evidence.

**Production HOLD.** PR #97 remains OPEN / DRAFT / UNMERGED.
