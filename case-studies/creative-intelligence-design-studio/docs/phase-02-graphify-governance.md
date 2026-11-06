# Phase 02 — Governed Graphify Integration

**Status:** Disposable synthetic Graphify extraction and source traceability passed. Phase 02.3 owner HOLD is confirmed; the INFERRED edge remains under review pending additional evidence. Production is not approved.  
**Release status:** Not approved for production.  
**Target:** A disposable, synthetic-only code fixture inside this Creative Studio module.

## Decision

Graphify v0.9.100 is the reviewed Phase 02 candidate. Source identity, release provenance, license, dependency profile and the published Fortran advisory are recorded in [Phase 02.1 Source & Version Intake](phase-02-1-source-intake.md). A separate owner approval for exactly one disposable GitHub-hosted synthetic run was consumed by run 41430984629. No repeat extraction is authorized by that approval. The only executed scan covered two synthetic Python files; it did not scan the KMH OIA repository root, MLCW source assets, learner records, private project documents, PDFs, images, audio, or video.

The policy is fail-closed. The scan root is fixed to graphify-sandbox; the allowed filesystem entries are .graphifyignore and Python files under src/. A Python validator enforces this boundary before an operator can consider a run. The Graphify ignore rules and CLI exclusions are defense in depth, not the primary positive allowlist.

## Current implementation

- contracts/graphify-scope-policy.json — provider identity, fixed scan root, exact allowlist, deny patterns, execution switches, and human gates.
- graphify-sandbox/.graphifyignore — secret/private-data exclusions for the disposable fixture.
- graphify-sandbox/src/ — two synthetic Python files with an explicit import and function call to test source traceability.
- scripts/validate_graphify_scope.py — checks the exact root, allowlist, denied paths, allowed extensions, symlinks, fixture completeness and disabled execution flags.
- scripts/validate_graphify_output.py — checks extracted graph source paths, line references, edge endpoints and cross-file evidence.
- scripts/review_graphify_edges.py — creates an EXTRACTED-only candidate from a hash-pinned review manifest without mutating raw graph evidence.
- tests/ — scope, extraction-traceability and controlled-promotion guard tests.
- artifacts/phase-02-3/ — extracted-only candidate graph and machine-readable review report; immutable raw Graphify graph remains separately in original workflow artifact 13134475847.

## Data-flow boundary

Graphify's code-only extraction uses deterministic local AST parsing and skips the separate model-backed semantic pass for documents and media. The completed disposable run used --code-only with a clean process environment containing no model credentials. No PDF, image, audio, video, private Markdown or learner content entered the scan. The output was external to the scan root and uploaded as a short-retention evidence artifact. Any future document/media experiment requires a separate data-flow review and explicit data-owner approval.

## Upstream intake

- Official source: https://github.com/Graphify-Labs/graphify
- Official package name: graphifyy (the CLI command is graphify).
- See [Phase 02.1 Source & Version Intake](phase-02-1-source-intake.md) for the reviewed candidate v0.9.100, exact release commit, PyPI wheel checksum, Apache-2.0 license, dependency profile and advisory evidence.
- The baseline graphify-scope-policy.json remains preflight-only. The one-time execution authority was recorded separately in graphify-disposable-pilot-approval.json, pinned to v0.9.100, consumed by run 41430984629 and does not grant local, assistant, global-graph or production permissions.
- Do not register the assistant skill, install project hooks, or add the project to a global graph during this initial code-only test.
- Do not use .graphifyinclude; current Graphify documentation states that it is no longer supported.

## Disposable execution — completed once

One project-owner approval for an ephemeral synthetic-only run was recorded and consumed. GitHub Actions run [41430984629](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41430984629) verified the pinned Graphify v0.9.100 source and uv.lock blob, installed the frozen base runtime in a temporary runner environment, copied exactly two synthetic Python files plus .graphifyignore, performed code-only extraction without model credentials, generated the graph and passed traceability validation. The graph and report are preserved in artifact [13134475847](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41430984629/artifacts/13134475847).

The run produced 12 nodes and 17 edges. Six edges connected the two fixtures; the traceability validator returned zero errors. The workflow's overall result is marked failed only because its final explicit cleanup shell step did not receive WORK_ROOT. The runner VM itself was ephemeral and disposed by GitHub after the job. The cleanup command has since been corrected, automatic push triggering has been removed, and the consumed approval prevents another extraction run.

No further Graphify installation or extraction is authorized by the consumed one-run approval.

## Acceptance gates

**Dependency audit:** [Run 41423529714](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41423529714) passed hash-enforced PyPI and OSV scans of the exact frozen Graphify v0.9.100 base-runtime lock snapshot. Both reported no known vulnerabilities. [Evidence artifact 13129919973](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41423529714/artifacts/13129919973).

**Actual disposable Graphify execution:** [Run 41430984629](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41430984629) installed v0.9.100 in an external temporary virtual environment, extracted the two synthetic Python fixtures without model credentials, and passed graph traceability validation. Result: 12 nodes, 17 edges, 6 cross-file relationships, 16 EXTRACTED and 1 INFERRED edge, zero validator errors. [Artifact 13134475847](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41430984629/artifacts/13134475847).

**Latest PR-head CI (2026-11-02, commit `82af65cc92b7c52504067da31b65dc7198fd8659`):**
- Creative Studio QA [41435935271](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41435935271): SUCCESS — 44/44 tests.
- KMH OIA Tests [41435935317](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41435935317): SUCCESS — 462/462 tests and performance baseline.
- KMH OIA Validation [41435935325](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41435935325): SUCCESS — repository validation, tests, performance evidence and deployment evidence bundle.
- Dependency audit [41435935339](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41435935339): SUCCESS.

| Gate | Required evidence | Current state |
|---|---|---|
| G0 — Source, license, known advisory and frozen base-runtime dependency audit | Official v0.9.100 source provenance and hash-enforced PyPI/OSV audit | PASS |
| G1 — Scope guard and automated tests | Preflight validator and 36 Creative Studio tests | PASS |
| G2 — Isolated code-only extraction | Graph generated from only two synthetic Python fixtures on a disposable runner | PASS — 12 nodes, 17 edges |
| G3 — Source traceability | Source-backed nodes and edges have valid file/line provenance; cross-file evidence exists | PASS — 6 cross-file edges; 0 validator errors |
| G4 — Human graph review | Source-level analysis of inferred edges and project-owner confirmation | Owner decision CONFIRMED — keep the INFERRED `uses` edge under review; do not promote; gather more evidence. See Phase 02.3 report. |
| G5 — Owner authorization | Single disposable synthetic-run approval | PASS — consumed by run 41430984629; no repeat run authorized |

The disposable workflow run is marked FAILED solely because its final explicit cleanup shell step did not receive the `WORK_ROOT` variable. Extraction, graph generation, traceability validation and artifact upload passed. GitHub-hosted runner VMs are ephemeral and are destroyed by GitHub after the job; the cleanup command is corrected to use `$RUNNER_TEMP`. Automatic push triggering is removed and the approval contract is marked consumed.


**Phase 02.3 controlled review:** The raw graph SHA-256 is pinned to `c5ad7ea7fdd6b6c65c81726a0aec51c5bead7a3cf29ff85a59051eb6bd95abeb`. The only INFERRED edge at `outfit_flow.py:L6` duplicates an EXTRACTED `references / parameter_type` relationship on the same source, target and line. Owner-confirmed decision: HOLD it out of the EXTRACTED-only candidate, retain it in raw evidence, do not call it a proven false positive, and gather more evidence. The EXTRACTED-only candidate contains 12 nodes and 16 edges; candidate SHA-256 `c2053e83445e8b4c94d5c29a9a3ef816ccf15561c5a76cd8139e2412584123c1`. The candidate graph and machine-readable promotion report are stored under artifacts/phase-02-3/. Owner HOLD confirmation is recorded; independent semantic review remains OPEN. See [Phase 02.3 review](phase-02-3-human-graph-review.md).

## Hard stop conditions

Stop and reject the run if the validator fails, a symlink or unapproved file is present, output includes a sensitive path, any model backend is selected, the scanner targets a path outside graphify-sandbox, or a reviewer cannot resolve an edge to source evidence. Preserve only sanitized QA findings; do not commit generated graph output.

## Relationship to KMH OIA

Phase 02 remains an adapter-level experiment beneath the existing KMH OIA governance boundary. It does not modify the OIA runtime, create a second core, install an agent automatically, or authorize deployment. Phase 02 has now completed a disposable Graphify extraction experiment and an EXTRACTED-only review candidate. This is not an integration into the KMH OIA production runtime and is not a production release.
