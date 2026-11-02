# Phase 02 — Governed Graphify Integration

**Status:** Guarded preflight scaffold implemented; Graphify installation and indexing are NOT RUN.  
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

**Dependency audit evidence:** Latest run [41423344454](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41423344454) passed hash-enforced PyPI and OSV scans of the exact frozen Graphify v0.9.100 base-runtime lock snapshot. Both returned no known vulnerabilities. [Evidence artifact 13131340453](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41423344454/artifacts/13131340453).

**Latest CI evidence (2026-11-02):** Creative Studio QA run [41423333319](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41423333319) passed 28 tests and diff check. KMH OIA Tests run [41423344597](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41423344597) passed 462 tests and performance baseline. KMH OIA Validation run [41423344325](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41423344325) passed repository validation, tests, performance evidence and the deployment evidence bundle.

| Gate | Required evidence | Current state |
|---|---|---|
| G0 — Source and version intake | Official source, license, exact candidate, known advisory and frozen base-runtime dependency audit | PASS — dependency audit run 41422855820; install approval remains pending |
| G1 — Scope guard | Validator and unit tests pass in GitHub CI | PASS — Creative Studio QA run 41423333319; 28/28 tests and diff check passed |
| G2 — Isolated code-only extraction | Reproducible graph from synthetic Python fixture | NOT RUN |
| G3 — Source traceability | Sampled EXTRACTED edges resolve to source file/line | NOT RUN |
| G4 — False-connection review | Expected import/call edges present; unsupported links rejected; INFERRED edges separately reviewed | NOT RUN |
| G5 — Owner authorization | Technical owner and data owner approve any scope expansion | PENDING |

## Hard stop conditions

Stop and reject the run if the validator fails, a symlink or unapproved file is present, output includes a sensitive path, any model backend is selected, the scanner targets a path outside graphify-sandbox, or a reviewer cannot resolve an edge to source evidence. Preserve only sanitized QA findings; do not commit generated graph output.

## Relationship to KMH OIA

Phase 02 remains an adapter-level experiment beneath the existing KMH OIA governance boundary. It does not modify the OIA runtime, create a second core, install an agent automatically, or authorize deployment. The current state is a CI-testable preflight scaffold — not a completed Graphify integration and not a production release.
