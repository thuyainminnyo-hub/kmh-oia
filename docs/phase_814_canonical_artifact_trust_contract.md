# Phase 814 — Canonical Artifact Trust Contract Reconciliation

Date: 2026-10-21

## Implemented

- Unified the protected signer allowlist and provenance test fixture on `.github/workflows/trusted-build.yml`.
- Added a regression test that fails if these workflow paths drift apart again.
- Updated Phase 812/813 records to identify the remaining blocker explicitly.

## Source evidence

The repository tree was inspected recursively at commit `5435025b5c47241634f8ac9847c9802611c08c8a`. No file named `classifier.bin` or `policy.bin` exists in the repository, and there is no `.github/workflows/trusted-build.yml` producer workflow. `src/autonomy_policy.py` is Python source and must not be relabeled as a compiled classifier or treated as a production binary.

## Next gate

Define the real producer inputs/outputs for the KMH OIA runtime before implementing the producer workflow. Once agreed in code, the producer must emit the exact artifact name `kmh-oia-runtime-bundle`, with documented artifact layout, on the exact source SHA, and upload it via GitHub Actions. The signer already checks run identity, source SHA, run success, artifact ID/name/digest and downloaded ZIP digest.

## Decision

This reconciles the current trust-path contract but does not complete the producer pipeline. No production signing/deployment was run. PR #97 remains OPEN / DRAFT / UNMERGED. **Production HOLD.**