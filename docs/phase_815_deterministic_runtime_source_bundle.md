# Phase 815 — Deterministic Runtime Source Bundle & Signed Provenance

Date: 2026-10-21

## Implementation

- Added `.github/workflows/trusted-build.yml`. On pushes to `main`, it checks out the exact SHA, installs the declared dependencies, compiles source/test/script modules, runs deployment preflight and the full unit suite, builds a deterministic source tarball, validates its manifest and uploads artifact `kmh-oia-runtime-bundle` with 90-day retention. The producer has no production signing key or protected production environment.
- Added `scripts/package_runtime_bundle.py`. It packages `src/` and `requirements.txt`, records `SOURCE_REVISION`, creates `MANIFEST.json` with a SHA-256 for each packaged file, and normalizes tar metadata/gzip timestamp for reproducible output.
- Added `scripts/validate_runtime_bundle.py`, which rejects unsafe/duplicate archive paths, wrong source revisions, missing files, malformed manifests, file-list mismatches and content digest mismatches.
- Added `src/runtime_bundle_attestation.py`, `src/runtime_bundle_attestation_io.py` and `scripts/create_runtime_bundle_attestation.py`. The signed statement binds the source bundle digest, source revision, producer run ID, artifact ID/name, artifact-service digest, issuer, subject, key ID and issuance time.
- Updated the protected signer to verify the producer run and artifact through GitHub APIs, download by immutable artifact ID, verify the artifact service ZIP digest, validate the source bundle and sign the actual bundle digest. It no longer labels files as `classifier.bin` or `policy.bin`.

## Verification boundary

Unit tests cover deterministic packaging, manifest integrity, provenance metadata binding, signature verification, mismatched digests/source SHA, create-only evidence output and workflow contract guards. GitHub CI still needs to pass on this commit.

The bundle is a Python source release artifact; it is not a compiled model and it is not proof of deployment. Production signing depends on GitHub `production-attestation` reviewers/secrets and production verifier public-key allowlists that CI cannot confirm. Real deployment, external provider authenticity, rollback rehearsal and independent human review remain outstanding.

PR #97 remains OPEN / DRAFT / UNMERGED. **Production HOLD.**
