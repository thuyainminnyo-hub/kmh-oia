# Phase 1011.11 — Reproducible Python Dependency Lock & Provenance Assurance

Date: 2026-10-30

## Objective

Turn the direct Python CI tooling pins into a complete, hash-verified dependency closure and prove that a clean CPython 3.12 environment can be reconstructed offline from the downloaded, hash-verified wheel set.

This lock is deliberately scoped to the existing GitHub Actions test target: `ubuntu-latest`, x86_64, CPython 3.12. It is not represented as a cross-platform runtime lock.

## Dependency graph

Direct CI inputs remain in `requirements.txt`:

- `jsonschema==4.26.0`
- `PyYAML==6.0.3`

The reviewed resolved closure in `requirements-ci.lock` is:

| Distribution | Locked version | Role |
|---|---:|---|
| jsonschema | 4.26.0 | Direct CI schema validator |
| PyYAML | 6.0.3 | Direct CI YAML validator |
| attrs | 25.4.0 | jsonschema / referencing dependency |
| jsonschema-specifications | 2025.9.1 | jsonschema dependency |
| referencing | 0.37.0 | jsonschema / specifications dependency |
| rpds-py | 0.30.0 | jsonschema / referencing dependency |
| typing-extensions | 4.15.0 | Python 3.12 marker dependency of referencing |

All seven distributions are exact-pinned and have a SHA-256 hash for the wheel supported by the target CI platform. The lock uses `--require-hashes` and `--only-binary=:all:`; no source build or unpinned build-system dependency is permitted in this CI installation path.

## Implemented

1. `requirements-ci.lock`
   - Exact direct and transitive dependency versions.
   - SHA-256 artifact hash for every locked distribution.
   - Target scope explicitly documented as CPython 3.12 / ubuntu-latest x86_64.
   - The existing `requirements.txt` remains the direct dependency input and is checked against the lock.

2. `scripts/verify_python_lock.py`
   - Fails closed on missing, duplicate, malformed, unhashed, extra, or version-drifted lock entries.
   - Verifies every CI workflow that installs Python requirements uses the lock with `--require-hashes` and `--only-binary=:all:`.
   - Verifies direct pins in `requirements.txt` are represented at the same versions in the lock.
   - Can verify the installed package versions, detect unexpected distributions, and record SHA-256 evidence for wheelhouse files.

3. `tests/test_python_lock.py`
   - Tests valid lock acceptance, missing hash rejection, unlocked workflow detection, and direct-pin drift rejection.

4. CI workflow migration
   - `test.yml`, `validation.yml`, `prompt-library-schema-qa.yml`, `action-dependency-assurance.yml`, and `reusable-workflow-sha-audit.yml` now install from `requirements-ci.lock`.
   - The reusable workflow audit explicitly selects Python 3.12 and its action reference is reflected in `.github/workflows/actions.lock`.
   - The action dependency workflow runs the lock contract verifier and adversarial tests.

5. Clean reconstruction job in `test.yml`
   - Creates a new virtual environment.
   - Downloads only wheels with hash verification.
   - Reinstalls with `--no-index` from the local wheelhouse using the same hash lock.
   - Runs `pip check`.
   - Verifies the installed package versions and wheel hashes.
   - Uploads `python-lock-provenance.json` as a CI artifact.

## Reproducibility acceptance criteria

The new job must prove all of the following on the PR head SHA:

- Lock syntax and package set: PASS.
- Every lock entry exact-pinned and SHA-256 hashed: PASS.
- All workflow installation consumers use the lock and enforce hashes/binary wheels: PASS.
- Wheelhouse contains exactly seven files whose SHA-256 digests are in the lock: PASS.
- Offline installation from wheelhouse succeeds: PASS.
- `pip check` reports no broken requirements: PASS.
- Installed package set and versions equal the reviewed lock: PASS.
- Provenance artifact records lock digest, Python/platform identity, installed package versions, and wheel file hashes.

No reproducibility PASS should be claimed until the new GitHub Actions run completes and its artifact is inspected.

## Scope and limitations

- This lock is for the current Ubuntu x86_64 / CPython 3.12 CI environment. Windows, macOS, ARM64, other Python versions, and application deployment images need separately generated and verified locks.
- It locks Python CI tooling, not application runtime dependencies. Phase 1011.10's static runtime source import audit remains a separate control.
- It does not lock GitHub Actions' bundled Node.js packages or runner image contents.
- It does not prove packages are vulnerability-free or benign. Hash verification proves downloaded artifact byte identity against the committed digest; it does not prove source safety.
- pip itself is provided by the Python 3.12 virtual-environment bootstrap. It is installer tooling, not one of the application CI dependencies.
- The project-root license decision remains OWNER_DECISION_REQUIRED from Phase 1011.10.

## Upstream evidence sources

- pip repeatable installs and version pinning: https://pip.pypa.io/en/stable/topics/repeatable-installs/
- pip hash-checking mode and binary-only guidance: https://pip.pypa.io/en/stable/topics/secure-installs/
- PyPI artifact integrity and SHA-256 verification: https://docs.pypi.org/using-pypi/package-security/package-integrity/
- jsonschema 4.26.0 release files and hashes: https://pypi.org/pypi/jsonschema/4.26.0/json
- PyYAML 6.0.3 release files and hashes: https://pypi.org/pypi/PyYAML/6.0.3/json
- attrs 25.4.0 release files and hashes: https://pypi.org/pypi/attrs/25.4.0/json
- jsonschema-specifications 2025.9.1 release files and hashes: https://pypi.org/pypi/jsonschema-specifications/2025.9.1/json
- referencing 0.37.0 release files and hashes: https://pypi.org/pypi/referencing/0.37.0/json
- rpds-py 0.30.0 release files and hashes: https://pypi.org/pypi/rpds-py/0.30.0/json
- typing-extensions 4.15.0 release files and hashes: https://pypi.org/pypi/typing-extensions/4.15.0/json

## Governance decision

- Implementation: ready for CI validation.
- CI dependency installation: HOLD until the new reproducibility workflow succeeds and evidence is reviewed.
- Production release: HOLD; this phase only hardens the CI tooling dependency chain and does not close the project-license, remote-action transitive, deployment-image, or application-runtime release gates.
