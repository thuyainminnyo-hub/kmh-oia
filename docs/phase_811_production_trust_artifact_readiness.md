# Phase 811 — Production Trust & Artifact Readiness Verification

Date: 2026-10-21

## Finding from source inspection

The current production attestation workflow accepts repository-relative classifier and policy paths and checks that the files exist and are non-empty after checking out the selected `main` source revision. This is a useful safety guard, but it is not a trusted build-artifact contract. It does not fetch an immutable artifact from an independently identified build run, compare a producer run SHA and workflow identity, or prove that the file was emitted by the approved build pipeline.

A signature over measured bytes establishes that the configured private key signed those bytes. It does not independently authenticate the origin of those bytes.

## Phase 811 changes

- Strengthen the workflow's relative path validation by resolving paths under the checkout root and rejecting symlink/path escapes.
- Expand static tests to assert manual-only execution, exact main/manual gate, protected Environment use, scoped secret use, non-empty and checkout-confined paths, run-scoped evidence output, and explicit refusal to equate source-tree files with build provenance.
- Keep Phase 810's source-controlled workflow guarantees separate from GitHub's external Environment configuration.

## Required external validation, not claimed complete

1. A repository administrator must configure and verify required reviewers and environment-scoped secret/variables on `production-attestation`.
2. The production verifier must be provisioned with the matching public key, exact key identifier, issuer and subject allowlists, plus a pinned expected source revision.
3. The team must define an immutable build artifact handoff contract: approved workflow identity, run ID, source SHA, artifact name/ID, digest(s), retention, and verification of the source run before signing.
4. A substantive independent human review is still required for PR #97.
5. Runtime provider authenticity, target-host deployment evidence, real-data migration/rollback rehearsal and release sign-off remain outstanding.

## Status

PR #97 remains OPEN / DRAFT / UNMERGED. No independent submitted reviews or review threads are recorded at this checkpoint.

**Release decision: Production HOLD.** Passing repository CI is not production readiness or deployment proof.
