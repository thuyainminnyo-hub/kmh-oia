# Phase 810 — Protected Release Workflow & Independent Review

Date: 2026-10-21

## Implemented in this source branch

- Manual `workflow_dispatch` trigger only; the workflow condition restricts execution to `refs/heads/main`.
- Explicit classifier/policy artifact paths are required and validated as safe repository-relative, existing, non-empty files.
- Signing waits for preflight and targets the GitHub Environment `production-attestation`.
- The private key is passed only to the signing step from an environment-scoped secret; no private key is committed or printed.
- Attestation output uses the existing create-only writer and is uploaded as a run-scoped CI artifact, not a deployment receipt.
- Static regression tests cover the trigger, protected environment, preflight dependency, artifact guards and secret handling.

## Repository administrator prerequisites — not verified by this commit

Configure the GitHub Environment `production-attestation` with required reviewers and environment-scoped values:

- Secret: `KMH_OIA_ATTESTATION_PRIVATE_KEY_B64` — 32 raw Ed25519 seed bytes encoded as base64. Never commit it.
- Variable: `KMH_OIA_ATTESTATION_KEY_ID` — non-placeholder key identifier.
- Variable: `KMH_OIA_ATTESTATION_ISSUER` — exact trusted issuer.
- Variable: `KMH_OIA_ATTESTATION_SUBJECT` — exact repository/main subject expected by the consumer trust policy.

Provision the corresponding public key and exact issuer/subject allowlists separately in the production verifier trust root. Do not reuse ephemeral test keys.

## Remaining production gates

1. A production build artifact contract has not yet been established. The workflow requires explicit paths and does not claim that this repository builds or deploys production classifier/policy artifacts.
2. Environment reviewers, protection rules and secrets are external settings; this code change cannot prove they exist or are configured correctly.
3. A successful signature proves only that a trusted key signed measured bytes. It does not prove provider authenticity, runtime deployment, business outcome, rollback readiness or independent review.
4. A human reviewer must inspect PR #97 and provide a substantive independent review; automated tests cannot satisfy this requirement.
5. Run production signing only after administrator prerequisites and the artifact contract are agreed. Keep the release decision on HOLD until target-host evidence, provider authenticity, migration/rollback rehearsal and release sign-off are reviewed.

## Verification record for current source head

At head `665825487c4a2498b964f7b6d48edb84257c1191`, the repository's Tests and Validation GitHub Actions runs completed successfully. Validation jobs include `tests`, `performance-evidence`, `repository-validation`, and `deployment-evidence-bundle`. These are repository CI results only; the workflow does not prove that the external GitHub Environment has reviewers or secrets configured.

## Phase 809 wording correction

The signer measures and rejects empty artifact bytes before evaluating production run-context checks. The Phase 809 doc now records this order accurately; earlier wording that implied context checks happened before artifact measurement was stale.

**Decision: Production HOLD.**

PR: https://github.com/thuyainminnyo-hub/kmh-oia/pull/97
