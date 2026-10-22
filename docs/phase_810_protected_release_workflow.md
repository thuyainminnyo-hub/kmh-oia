# Phase 810 — Protected Release Workflow & Independent Review

Date: 2026-10-21

## Implemented in this source branch

- Manual `workflow_dispatch` trigger only; workflow job conditions restrict signing to `refs/heads/main`.
- Explicit classifier/policy paths are checked for safe relative paths, non-empty files, and resolution within the checked-out tree (including symlink escape rejection).
- Signing waits for preflight and targets the GitHub Environment `production-attestation`.
- The private key is passed only to the signing step from an environment-scoped secret; no private key is committed or printed.
- Attestation output uses the create-only writer and is uploaded as a run-scoped CI artifact, not a deployment receipt.
- Static regression tests check manual-only trigger, main-only guard, environment target, preflight ordering, path confinement, empty input rejection, and secret-scope rules.

## Repository administrator prerequisites — not verified by this commit

Configure the GitHub Environment `production-attestation` with required reviewers and environment-scoped values:

- Secret: `KMH_OIA_ATTESTATION_PRIVATE_KEY_B64` — 32 raw Ed25519 seed bytes encoded as base64. Never commit it.
- Variable: `KMH_OIA_ATTESTATION_KEY_ID` — non-placeholder key identifier.
- Variable: `KMH_OIA_ATTESTATION_ISSUER` — exact trusted issuer.
- Variable: `KMH_OIA_ATTESTATION_SUBJECT` — exact repository/main subject expected by the consumer trust policy.

Provision the corresponding public key and exact issuer/subject allowlists separately in the production verifier trust root. Do not reuse ephemeral test keys.

## Remaining production gates

1. The repository does not yet define a trusted immutable build artifact contract. The current inputs point at files in the checked-out `main` tree; path guards and a signature do not prove those files were emitted by a trusted build.
2. Environment reviewers, protection rules and secrets are external settings; source-controlled YAML cannot prove they exist or are correctly configured.
3. A successful signature proves only that the configured signing key signed measured bytes. It does not prove provider authenticity, runtime deployment, business outcome, rollback readiness or independent review.
4. A human reviewer must inspect PR #97 and provide a substantive independent review; automated tests cannot satisfy this requirement.
5. Run production signing only after administrator prerequisites and an immutable artifact contract are agreed. Keep release on HOLD until target-host evidence, provider authenticity, migration/rollback rehearsal and release sign-off are reviewed.

## Verification record

At head `31f97a0fc244772c3913bd3b742af6ef05c697dc`:
- [Tests #781 — SUCCESS](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/39624060842).
- [Validation #700 — SUCCESS](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/39624060869); tests, performance-evidence, repository-validation, and deployment-evidence-bundle succeeded.

These are repository CI results only; they do not prove GitHub Environment configuration or production deployment.

**Decision: Production HOLD.**

PR: https://github.com/thuyainminnyo-hub/kmh-oia/pull/97
