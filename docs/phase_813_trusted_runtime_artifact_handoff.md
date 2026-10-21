# Phase 813 — Trusted Runtime Artifact Handoff Contract

Date: 2026-10-21

Phase 813 changed the manual-only protected signer to verify producer run metadata via GitHub Actions APIs, require an immutable artifact ID/name/digest, download by artifact ID, compare the service ZIP digest and fail-closed instead of signing source-tree paths.

Phase 814 aligned the canonical producer workflow path. Phase 815 now provides `.github/workflows/trusted-build.yml`, which builds a deterministic source bundle after repository validation and uploads it as `kmh-oia-runtime-bundle`.

The signer validates the downloaded source bundle's embedded source revision and per-file manifest, then signs the SHA-256 of the actual `runtime-source-bundle.tar.gz` bytes using a dedicated `RuntimeBundleAttestation` statement. The statement binds source SHA, producer run ID, artifact ID, exact name, artifact service digest and bundle digest.

External GitHub Environment protection, production signing secrets, trusted public-key configuration, real runtime deployment, provider authenticity, rollback rehearsal and independent human review remain separate gates. CI does not verify those external controls. **Production HOLD.**


**The signed artifact attestation is not proof of deployment.** A valid signature authenticates only the attested bundle and provenance fields; target-host rollout and production outcome still require separate evidence.
