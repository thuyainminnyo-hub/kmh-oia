# Phase 816 — Deterministic Runtime Bundle Safety Regression Tests

Date: 2026-10-21

## Scope

Added packaging safety regression tests covering deterministic bytes across repeat builds, source revision and manifest digest binding, rejection of symlinked runtime source, duplicate archive entries, archive path escape, and refusal to overwrite an existing artifact.

The trusted build workflow emits a deterministic Python runtime source bundle (`runtime-source-bundle.tar.gz`) containing `SOURCE_REVISION` and `MANIFEST.json`. This is a source package, not a compiled model or proof of production deployment.

## Verification boundary

The tests and repository validation must pass on the exact Phase 816 commit before marking it CI-verified. The trusted build workflow needs to execute on `main` to produce a real eligible producer run and immutable artifact for the signer. No production signing is invoked by pull-request CI.

PR #97 remains OPEN / DRAFT / UNMERGED pending independent human review. **Production HOLD.**
