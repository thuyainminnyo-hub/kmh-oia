# Phase 803 — Runtime Artifact Byte Measurement

Date: 2026-10-21

## Delivered
Added `src/runtime_artifact_measurement.py` to calculate SHA-256 from actual file bytes and validate a pinned digest. The in-memory helper validates the exact byte payload intended for loading. Returned `MeasuredArtifact.content` preserves the bytes that were measured.

Added tests for measured file digests, matching pin acceptance, changed-byte rejection, invalid digest rejection, in-memory payload verification, and digest normalization.

## Trust boundary
Byte measurement proves only that measured bytes match a digest. It does not authenticate who supplied the bytes or prove signer identity. A maliciously supplied expected digest could still match malicious content. Production must separately validate signed provenance against a trusted root and load the exact measured byte payload; a mutable path should not be reopened after verification.

## Release gates
- Exact-head CI must pass for this change.
- Production-grade signature/provenance verification and trust-root configuration remain outstanding.
- Independent human review, real-data migration/rollback rehearsal, provider authenticity, actual deployment evidence, and release sign-off remain outstanding.

**Decision: Production HOLD.**

PR: https://github.com/thuyainminnyo-hub/kmh-oia/pull/97
