# Phase 813 — Trusted Runtime Artifact Handoff Contract

Date: 2026-10-21

This phase rewires the protected signer to require producer-run and immutable artifact metadata. It queries GitHub Actions APIs to verify the run and artifact, downloads by artifact ID, checks the ZIP digest, then signs the classifier and policy bytes.

## Canonical producer contract

The approved workflow path is `.github/workflows/trusted-build.yml` and the expected artifact name is `kmh-oia-runtime-bundle`. The path must match the provenance validator's allowlist fixture. This is a trust-policy declaration, not evidence the producer exists.

## Fail-closed condition

The referenced producer workflow has not been implemented yet, and the repository does not currently contain the promised `classifier.bin` and `policy.bin` outputs. Signing preflight will fail until a reviewed producer actually emits this exact bundle for the pinned source SHA.

The signer records producer run ID/source SHA, queries actual GitHub run and artifact metadata, downloads by immutable artifact ID, checks the digest and only then signs measured artifact bytes. It no longer accepts source-tree classifier/policy paths or labels the signing run as the build run.

## Verification boundary

Static regression tests cover workflow contracts. They do not prove external GitHub Environment protections, actual production secrets, live GitHub API behavior, or a real deployment. Production remains HOLD and PR #97 remains draft/unmerged pending independent review.

**Release decision: Production HOLD.**