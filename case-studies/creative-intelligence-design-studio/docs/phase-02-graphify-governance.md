# Phase 02 — Governed Graphify Integration

**Status:** Disposable synthetic Graphify extraction and source traceability passed. Phase 02.3 review candidate is prepared; project-owner confirmation is pending. Production is not approved.  
**Release status:** Not approved for production.  
**Target:** A disposable, synthetic-only code fixture inside this Creative Studio module.

## Decision

Graphify v0.9.100 is the selected Phase 02 candidate. Source identity, release provenance, license, dependency profile and the published Fortran advisory have been reviewed in [Phase 02.1 Source & Version Intake](phase-02-1-source-intake.md). Explicit owner approval is still required before installation or indexing. The first experiment is deliberately limited to deterministic Python AST extraction from two synthetic files. It must not scan the KMH OIA repository root, MLCW source assets, learner records, private project documents, PDFs, images, audio, or video.

The policy is fail-closed. The scan root is fixed to graphify-sandbox; the allowed filesystem entries are .graphifyignore and Python files under src/. A Python validator enforces this boundary before an operator can consider a run. The Graphify ignore rules and CLI exclusions are defense in depth, not the primary positive allowlist.

## Current implementation

- contracts/graphify-scope-policy.json — provider identity, fixed scan root, exact allowlist, deny patterns, execution switches, and human gates.
- graphify-sandbox/.graphifyignore — secret/private-data exclusions for the disposable fixture.
- graphify-sandbox/src/ — two synthetic Python files with an explicit import and function call to test source traceability.
- scripts/validate_graphify_scope.py — checks the exact root, allowlist, denied paths, allowed extensions, symlinks, fixture completeness, and disabled execution flags.
- tests/test_graphify_scope.py — negative tests for broad roots, allowlist widening, model backend activation, secret files, non-Python assets, and symlinks.
- The Creative Studio QA workflow runs the preflight validator and the existing unit-test suite.

## Data-flow boundary

Graphify documents deterministic local tree-sitter AST parsing for code and a separate semantic pass for documents and media. Documents, PDFs, and images can be sent to the active assistant model or a configured backend. Therefore:

1. The first run, after separate approval, must use code-only extraction and a disabled backend.
2. No PDF, image, audio, video, private Markdown, or learner content may enter this first test.
3. The command must set GRAPHIFY_BACKEND=none and use --code-only.
4. The output directory must be outside the repository and removed after evidence capture.
5. No auto-detected or paid model provider may be used.
6. Any later document/media experiment requires a separate data-flow review and explicit data-owner approval.

## Upstream intake

- Official source: https://github.com/Graphify-Labs/graphify
- Official package name: graphifyy (the CLI command is graphify).
- See [Phase 02.1 Source & Version Intake](phase-02-1-source-intake.md) for the reviewed candidate v0.9.100, exact release commit, PyPI wheel checksum, Apache-2.0 license, dependency profile and advisory evidence.
- The machine-readable policy records v0.9.100 as a candidate, not an approval. `approved_version` intentionally remains null; installation remains disabled.
- Do not register the assistant skill, install project hooks, or add the project to a global graph during this initial code-only test.
- Do not use .graphifyinclude; current Graphify documentation states that it is no longer supported.

## Operator procedure after approval

Run from a disposable workstation or container with filesystem access restricted to the task. The source snapshot below prevents the scanner from receiving any file beyond the three explicitly copied synthetic fixtures.

1. Confirm that the technical owner has explicitly approved v0.9.100 and the data owner has approved this exact fixture.
2. Verify the source tag resolves to commit `f5155badddaa3286c78a51653791131e9e2e4d29`.
3. In the exact release checkout, verify the upstream `uv.lock` blob SHA, then use the pinned uv 0.13.6 and `uv sync --frozen --no-dev --python 3.12`. Do not regenerate the lock or add extras.
4. Create an external temporary workspace and copy only the approved fixture files into a new scan root. Do not point Graphify at the repository or the original feature branch directory.
5. Make the snapshot read-only and verify it contains exactly three files before execution.
6. Run code-only extraction with model backend disabled and graph output stored outside the scan root. Do not execute `graphify install`, hook installation, MCP setup, or a model-backed semantic pass.

The exact commands are recorded in [Phase 02.1 Source & Version Intake](phase-02-1-source-intake.md). They are an operator runbook only and have NOT been run.

## Acceptance gates

**Dependency audit:** [Run 41423529714](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41423529714) passed hash-enforced PyPI and OSV scans of the exact frozen Graphify v0.9.100 base-runtime lock snapshot. Both reported no known vulnerabilities. [Evidence artifact 13129919973](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41423529714/artifacts/13129919973).

**Actual disposable Graphify execution:** [Run 41430984629](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41430984629) installed v0.9.100 in an external temporary virtual environment, extracted the two synthetic Python fixtures without model credentials, and passed graph traceability validation. Result: 12 nodes, 17 edges, 6 cross-file relationships, 16 EXTRACTED and 1 INFERRED edge, zero validator errors. [Artifact 13134475847](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41430984629/artifacts/13134475847).

**Latest PR-head CI (2026-11-02, commit `02b65c88`):**
- Creative Studio QA [41431490515](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41431490515): SUCCESS — 36/36 tests.
- KMH OIA Tests [41431490359](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41431490359): SUCCESS — 462/462 tests and performance baseline.
- KMH OIA Validation [41431490548](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41431490548): SUCCESS — repository validation, tests, performance evidence and deployment evidence bundle.
- Dependency audit [41431490286](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41431490286): SUCCESS.

| Gate | Required evidence | Current state |
|---|---|---|
| G0 — Source, license, known advisory and frozen base-runtime dependency audit | Official v0.9.100 source provenance and hash-enforced PyPI/OSV audit | PASS |
| G1 — Scope guard and automated tests | Preflight validator and 36 Creative Studio tests | PASS |
| G2 — Isolated code-only extraction | Graph generated from only two synthetic Python fixtures on a disposable runner | PASS — 12 nodes, 17 edges |
| G3 — Source traceability | Source-backed nodes and edges have valid file/line provenance; cross-file evidence exists | PASS — 6 cross-file edges; 0 validator errors |
| G4 — False-connection review | Human decision on inferred/ambiguous edges | OPEN — one INFERRED `uses` edge at `outfit_flow.py:L6`; see Phase 02.2 report |
| G5 — Owner authorization | Single disposable synthetic-run approval | PASS — consumed by run 41430984629; no repeat run authorized |

The disposable workflow run is marked FAILED solely because its final explicit cleanup shell step did not receive the `WORK_ROOT` variable. Extraction, graph generation, traceability validation and artifact upload passed. GitHub-hosted runner VMs are ephemeral and are destroyed by GitHub after the job; the cleanup command is corrected to use `$RUNNER_TEMP`. Automatic push triggering is removed and the approval contract is marked consumed.


**Phase 02.3 controlled review:** The raw graph SHA-256 is pinned to `c5ad7ea7fdd6b6c65c81726a0aec51c5bead7a3cf29ff85a59051eb6bd95abeb`. The only INFERRED edge at `outfit_flow.py:L6` duplicates an EXTRACTED `references / parameter_type` relationship on the same source, target and line. Recommendation: HOLD it out of the canonical candidate, without calling it a proven false positive. The EXTRACTED-only candidate contains 12 nodes and 16 edges; candidate SHA-256 `c2053e83445e8b4c94d5c29a9a3ef816ccf15561c5a76cd8139e2412584123c1`. Owner confirmation remains pending. See [Phase 02.3 review](phase-02-3-human-graph-review.md).

## Hard stop conditions

Stop and reject the run if the validator fails, a symlink or unapproved file is present, output includes a sensitive path, any model backend is selected, the scanner targets a path outside graphify-sandbox, or a reviewer cannot resolve an edge to source evidence. Preserve only sanitized QA findings; do not commit generated graph output.

## Relationship to KMH OIA

Phase 02 remains an adapter-level experiment beneath the existing KMH OIA governance boundary. It does not modify the OIA runtime, create a second core, install an agent automatically, or authorize deployment. The current state is a CI-testable preflight scaffold — not a completed Graphify integration and not a production release.
