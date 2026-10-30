# Phase 1011.10 — Runtime Dependency & License Governance Assurance

Date: 2026-10-30

## Objective

Separate KMH OIA application runtime dependencies from CI tooling and GitHub Actions, establish exact-tag license evidence for the currently inventoried direct dependencies, and keep unresolved legal/supply-chain questions visible as release gates.

## Repository evidence reviewed

- `requirements.txt` declares only `jsonschema==4.26.0` and `PyYAML==6.0.3`, and explicitly describes itself as minimal CI/tooling dependencies.
- No `pyproject.toml`, `setup.cfg`, `Pipfile`, `uv.lock`, `poetry.lock`, or `Dockerfile` was present at the reviewed branch.
- A static AST import inventory of the checked-in `src/` tree found only Python standard-library and first-party `src/` imports. Third-party imports of `jsonschema` and `yaml` occur in validation/audit tooling under `scripts/`, not in the application `src/` tree.
- `requirements-runtime.txt` therefore intentionally contains no third-party runtime distributions at this checkpoint. This is an explicit, testable statement about static imports, not a claim that dynamic imports, native dependencies, external services, or deployment-environment dependencies do not exist.

## Implemented

1. `scripts/audit_python_dependencies.py`
   - Parses Python AST under `src/`.
   - Classifies standard-library, first-party, and third-party imports.
   - Requires every statically detected third-party runtime import to have an exact `name==version` pin in `requirements-runtime.txt`.
   - Fails closed on syntax errors, missing manifest, unpinned requirements, and undeclared third-party imports.
   - Emits machine-readable JSON evidence and explicitly documents dynamic-import limitations.

2. `requirements-runtime.txt`
   - Records that no third-party Python runtime distribution is currently declared.
   - Future third-party runtime imports must be accompanied by exact pins.

3. `licenses/dependency-license-review.json`
   - Records upstream LICENSE file evidence at the exact eight GitHub Action references in the current lockfile.
   - Records release-specific license evidence for the two direct Python CI/tooling packages.
   - Stores upstream URLs and source blob SHAs for review traceability.
   - Does not invent a license for the KMH OIA project itself.

4. `scripts/validate_license_inventory.py`
   - Cross-checks unique SPDX package name/version pairs against the evidence register.
   - Fails if an external package has no verified license evidence.
   - Preserves an explicit owner decision requirement for the root project license.

5. `tests/test_runtime_dependency_audit.py` and `tests/test_license_inventory.py`
   - Positive and negative tests for undeclared imports, exact pins, distribution/import-name mapping, unreviewed package licenses, and missing project-license decisions.

6. Supply-chain CI runs both audits and uploads `runtime-dependency-evidence.json` and `license-review-evidence.json` alongside the original SPDX SBOM and source snapshot.

## Exact license evidence recorded

| Package / action reference | Version | License | Evidence |
|---|---|---|---|
| actions/attest | v4.2.2 | MIT | Exact-tag upstream LICENSE |
| actions/checkout | v4.4.0 | MIT | Exact-tag upstream LICENSE |
| actions/checkout | v7.0.1 | MIT | Exact-tag upstream LICENSE |
| actions/download-artifact | v7.0.0 | MIT | Exact-tag upstream LICENSE |
| actions/setup-python | v5.6.0 | MIT | Exact-tag upstream LICENSE |
| actions/upload-artifact | v4.6.2 | MIT | Exact-tag upstream LICENSE |
| actions/upload-artifact | v6.0.0 | MIT | Exact-tag upstream LICENSE |
| anchore/sbom-action | v0.24.0 | Apache-2.0 | Exact-tag upstream LICENSE |
| jsonschema | 4.26.0 | MIT | PyPI release metadata + source LICENSE |
| PyYAML | 6.0.3 | MIT | PyPI release metadata + source LICENSE |

The license register covers the upstream repository-level license for each action. It does not inventory licenses of bundled Node.js transitive packages inside those actions.

## Explicit unresolved gates

- **Project license:** No root `LICENSE` or `NOTICE` file was present. The project license is `UNDECLARED`; the repository owner must select and approve a license. The implementation intentionally does not choose one.
- **Python transitive closure:** `requirements.txt` contains direct CI/tooling pins only. It is not a resolved, hash-pinned transitive lockfile. A separate lock-generation/reproducibility step is still required.
- **GitHub Action bundled dependencies:** The workflow lockfile pins action repositories and their action-level dependencies, but the source-tree SBOM does not fetch or enumerate all bundled Node.js package dependencies within remote actions. A complete action-internal license/SBOM review remains separate work.
- **Dynamic/runtime deployment dependencies:** Static AST scanning does not detect importlib-based dynamic imports, plugins, native libraries loaded outside Python imports, subprocess-installed tools, runner images, or external services.
- **License compatibility:** Identifying upstream license texts is not legal advice and does not determine compatibility with the project's future distribution model.

## Governance decision

- Runtime source import inventory: PASS if CI reports no undeclared third-party imports.
- Direct external dependency license evidence: REVIEWED for the ten unique action/Python package versions listed above.
- Project-root license: OWNER_DECISION_REQUIRED.
- Transitive Python lockfile and action-internal package license inventory: REVIEW_REQUIRED.
- Production release: HOLD until owner licensing decision and remaining dependency/provenance gates are independently evidenced.

## Upstream references

- GitHub workflow dependency lockfiles: https://docs.github.com/en/enterprise-cloud@latest/actions/concepts/security/workflow-dependency-lockfiles
- GitHub SBOM export and generation: https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/export-dependencies-as-sbom
- jsonschema 4.26.0 release metadata: https://pypi.org/project/jsonschema/4.26.0/
- PyYAML 6.0.3 release metadata: https://pypi.org/project/PyYAML/6.0.3/
