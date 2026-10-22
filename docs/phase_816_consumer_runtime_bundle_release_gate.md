# Phase 816 — Consumer-Side Runtime Bundle Release Gate

Date: 2026-10-22

- Added `scripts/verify_runtime_bundle_release.py` to verify runtime source bundle bytes, embedded source revision, manifest hashes and a detached Ed25519 attestation before a caller accepts a release.
- The verifier requires externally observed producer run ID, artifact ID/name and GitHub artifact service digest, plus an explicit public-key trust map and exact issuer/subject allowlists. It has no network side effects and does not claim to verify deployment.
- Unit tests cover a valid signed bundle and rejection for modified bundle bytes, modified signature, wrong key, issuer, subject, source SHA, producer run ID, artifact ID and artifact digest, plus missing trust-root configuration.
- This is a standalone consumer API. The existing production evidence runtime/deployed entrypoint has not yet been wired to call it; production integration and public trust-root provisioning remain open.
- Exact-head CI and a follow-up audit are required before marking this phase verified. PR #97 remains OPEN / DRAFT / UNMERGED. **Production HOLD.**