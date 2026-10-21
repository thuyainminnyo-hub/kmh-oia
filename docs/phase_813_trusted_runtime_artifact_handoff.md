# Phase 813 — Trusted Runtime Artifact Handoff Contract

Date: 2026-10-21

This phase rewires the protected signer to require producer-run and immutable artifact metadata. It queries GitHub Actions APIs to verify the run and artifact, downloads by artifact ID, checks the ZIP digest, then signs the classifier and policy bytes.

## Fail-closed condition

The only allowed producer workflow path is `.github/workflows/trusted-runtime-build.yml` and the only expected artifact name is `kmh-oia-runtime-bundle`. These are explicit trust-policy values, not evidence the producer exists. The referenced producer workflow has not been implemented yet, so signing preflight will fail until the producer is added, reviewed, and emits this exact bundle for the pinned source SHA.

The signer now records the producer run ID and source SHA instead of using its own signing run ID as the build run. It no longer accepts source-tree classifier/policy paths.

## Verification boundary

Static regression tests cover workflow contracts. They do not prove external GitHub Environment protections, actual production secrets, live GitHub API behavior, or a real deployment. Production remains HOLD and PR #97 remains draft/unmerged pending independent review.
