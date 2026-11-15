# Phase 2.2 — Committed Python CI Lockfile & Bootstrap Trust Boundary

## Current evidence reviewed
Source: the dependency-security-evidence artifact from PR #205, workflow run 42158297263, candidate head 39ff19fdb8e590ba9ed3a69f2121df74e194b390.

- The generated lock is specific to Python 3.12 on the Ubuntu GitHub-hosted runner used by the workflow.
- The requirements lock contains 32 pinned package entries and SHA-256 hashes.
- The lock ends with pip-tools' warning that `pip` was not pinned because it is treated as an unsafe requirement.
- The current workflow installs `pip-tools==7.6.2` before generating the lock, so the lock does not secure that bootstrap operation.
- The workflow subsequently installs the generated lock with `--require-hashes` and `--only-binary=:all:`.
- The artifact SBOM describes the complete installed CI environment and contains 40 components; all 33 locked dependency package/version pairs from the earlier artifact reconciliation were present in that SBOM.
- The lock artifact is generated at run time, not committed as a reviewed source-controlled lockfile.

## Proposed implementation

1. Generate a fresh lock on the exact target environment: CPython 3.12, Ubuntu runner, and the same pip resolver configuration used by CI.
2. Generate with `pip-compile --generate-hashes --allow-unsafe` so the unsafe `pip` requirement is represented and pinned in the lock where supported. Review the resulting `pip` pin explicitly; do not assume the flag alone proves the bootstrap interpreter itself is trusted.
3. Commit both `requirements-ci.in` and `requirements-ci.lock` to the candidate branch. Record the Python, OS, pip-tools version, generation command, and generation date in the lock header or adjacent documentation.
4. Remove `pip-tools` installation and lock generation from ordinary PR CI. CI should install the committed lock directly with:
   ```bash
   python -m pip install --require-hashes --only-binary=:all: -r requirements-ci.lock
   ```
5. Keep audit and SBOM generation as separate checks:
   - `pip-audit --require-hashes -r requirements-ci.lock`
   - `pip-audit --local`
   - Generate CycloneDX SBOM from the installed environment.
   - Compare normalized locked package/version pairs against SBOM components and fail on missing locked packages.
6. Create a separate deliberate lock-update workflow or documented maintainer command. Lock updates must be reviewed as code changes; CI must verify staleness rather than silently resolving a new dependency graph on every PR.
7. Treat other Python versions, operating systems, and architectures as separate target environments until evidence shows a common wheel/hash lock works for all supported targets.

## Bootstrap trust boundary
A committed hash lock protects downloaded distributions after the lock has been reviewed. It does not automatically establish trust in the already-installed Python/pip bootstrap used to perform the first installation. Document the runner-provided Python and pip as a trusted base image boundary, audit the complete installed environment, and consider a separately controlled bootstrap toolchain if stronger provenance is required.

## Acceptance criteria
- Lock file is committed, reviewed, and generated from a documented target environment.
- Every installable requirement is pinned and hash-covered; no unresolved unsafe requirement warning remains without an explicit documented exception.
- PR CI does not run pip-tools or regenerate the dependency graph.
- Hash-verified wheel-only installation succeeds from the committed lock.
- pip-audit checks both the lock and installed environment.
- SBOM reconciliation fails on any missing locked package/version.
- All relevant checks pass on the exact candidate head SHA.
- Independent reviewer approves the lock and bootstrap boundary.
- No merge, release, or production deployment occurs without separate owner approval.

## Governance
This is a design and implementation checklist for a sandbox candidate. It is not evidence that Phase 2.2 has been implemented or that production security has been established.
