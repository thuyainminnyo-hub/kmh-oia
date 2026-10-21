# Phase 801 — Production Artifact Identity & Independent Verification

Date: 2026-10-21

## Change
Trusted learning admission now requires two externally supplied immutable artifact SHA-256 digests:
- classifier artifact digest
- policy artifact digest

The service accepts a 64-character hexadecimal SHA-256 value, optionally prefixed by `sha256:`; it normalizes to lowercase. Missing or invalid digests fail closed before classifier execution. Both digests are included in the canonical admission fingerprint and the admission audit event. Reusing the same admission identity with a different classifier or policy digest is rejected before reclassification.

## Verification boundary
The constructor digest values must be generated and verified by a trusted build/release process. A caller-supplied string alone is not proof that the running bytes match it. Production wiring still needs a trusted artifact resolver/attestation check that binds the digest to the loaded classifier and policy bytes.

## Tests added
- missing digests fail closed
- malformed digest fails closed
- changed classifier digest conflicts under the same admission key
- changed policy digest conflicts under the same admission key
- unchanged artifact digests preserve idempotent retry

## Release gates still open
- PR #97 remains draft and unmerged until independent human review.
- Exact-head CI must pass for this change.
- Real production artifact provenance/attestation and actual runtime bytes must be independently verified.
- Migration/recovery requires controlled real-data rehearsal and rollback evidence.
- Actual deployment, authenticated external provider evidence, outcome review, and release sign-off are not proved by CI alone.

**Decision: Production HOLD.**

PR: https://github.com/thuyainminnyo-hub/kmh-oia/pull/97
