# SEC-241-01 — Snapshot publication path hardening (review specification)

Status: **OPEN / NOT VERIFIED**. This document is a remediation specification, **not** a security fix or production authorization.

## Evidence and scope

At PR #241 HEAD `52f6ebf042055cbb2ffb1fa35e9949163910a8e1`, `src/verified_snapshot_store.py` performs no-follow descriptor-relative reads (lines 81–184) but uses path-based publication in `put_bytes` (lines 212–254): `mkdir`, `mkstemp`, `os.link`, and `unlink`. The exact exploitability depends on whether an attacker can modify snapshot-store directories. No exploit has been demonstrated.

## Proposed minimal security change

1. Document and enforce a **trusted, privately writable store root** with explicit ownership/permissions and deployment checks. Reject untrusted or symlinked directory components where supported; do not silently follow mutable directories.
2. Bind staging, blob, and metadata operations to verified directory descriptors; use `dir_fd`-relative creation/link/unlink where supported. Fail closed on unsupported platforms instead of silently falling back to path-based operations.
3. Preserve the current digest, byte-length, no-follow read, metadata binding, and fsync guarantees. Avoid overwriting an existing content-addressed blob or artifact metadata.
4. Define crash consistency for a blob published before metadata. Orphan blobs must not be represented as admitted evidence; implement bounded, auditable cleanup only after approval.
5. Add deterministic tests for staging-directory symlink substitution, blob-parent symlink substitution, metadata-directory substitution, concurrent publication, and failure between blob and metadata publication. Include platform skip/fail-closed expectations.
6. Independently review the exact changed HEAD, rerun CI and targeted adversarial tests, and attach reproducible logs. Re-review PR #147 scope (MLCW files) separately.

## Acceptance gates

- [ ] Filesystem trust model and supported platforms documented
- [ ] Descriptor-bound publication implemented and reviewed
- [ ] Negative/race regression tests PASS on exact HEAD
- [ ] Exact-head CI PASS and independent security approval
- [ ] Authorized live ComfyUI output, integrity evidence, immutable audit, independent QA, and owner release authorization

**NO MERGE / NO DEPLOY / PRODUCTION HOLD.**
