# Phase 02.2 — Graphify Disposable Execution

Approval: Consumed single-run project-owner approval, recorded 2026-11-02.
Candidate: Graphify v0.9.100, source commit f5155badddaa3286c78a51653791131e9e2e4d29.
Input scope: Only src/contract_guard.py and src/outfit_flow.py, copied into an external runner directory.
Execution boundary: No local installation, assistant skill, Git hook, MCP server, model API, global graph, OIA production runtime or production deployment.

## Workflow procedure

1. Validate the separate single-run approval contract and existing preflight source-scope guard.
2. Start a fresh GitHub-hosted ubuntu-24.04 runner.
3. Clone the official Graphify source at v0.9.100 and verify the exact commit and uv.lock Git blob.
4. Use uv 0.13.6 and uv sync --frozen --no-dev --python 3.12 in a virtual environment under the runner temporary directory. No optional extras or development dependencies are requested.
5. Copy exactly the two synthetic Python files and the Graphify ignore file into a separate scan snapshot. Make the snapshot read-only and write a SHA-256 manifest.
6. Run graphify extract with --code-only --no-dedup --no-cluster and an output directory outside the scan root. The process receives a clean environment with no model credentials.
7. Run validate_graphify_output.py against the generated graph.json.
8. Upload the graph and sanitized traceability report for 14 days, then run the explicit temporary-workspace cleanup step. GitHub disposes of the hosted runner VM after the job.

## Traceability acceptance checks

- The graph JSON contains node and edge arrays.
- Node IDs are unique and every edge endpoint resolves.
- Source-backed nodes and edges refer only to the two approved source files.
- Every source-backed node and edge line reference exists within the actual source file.
- Required symbols appear in the correct source files: DesignToken, is_approved_token and select_outfit.
- At least one cross-file edge connects the two fixtures.
- Confidence labels are restricted to EXTRACTED, INFERRED and AMBIGUOUS.
- INFERRED and AMBIGUOUS edges are reported for human review and never automatically promoted to facts.

## Actual execution result

Workflow run [41430984629](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41430984629) executed Graphify v0.9.100 on a GitHub-hosted ubuntu-24.04 runner.

- Source commit and uv.lock blob pin checks: PASS.
- Temporary venv installation from the frozen upstream source: PASS; installed package version 0.9.100.
- External scan snapshot: exactly three files (.graphifyignore plus the two synthetic Python fixtures); snapshot read-only; SHA-256 manifest created.
- Code-only extraction: PASS.
- Graph JSON: 12 nodes, 17 edges.
- Cross-file links: 6.
- Confidence: 16 EXTRACTED, 1 INFERRED, 0 AMBIGUOUS.
- Traceability validator: PASS, zero errors; source nodes and source lines stayed within the two-file allowlist.
- One unanchored external-reference node represents the standard-library `dataclasses` import and was not counted as source-backed evidence.
- One INFERRED `uses` edge connects `select_outfit()` to `DesignToken` at `outfit_flow.py:L6`. It appears to overlap with the EXTRACTED type-reference edge at the same line and is flagged for manual false-connection review, not promoted to a fact.
- Evidence artifact [13134475847](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41430984629/artifacts/13134475847) uploaded successfully.

**Workflow conclusion:** The overall job is marked FAILED only because the final explicit cleanup shell step did not receive the `WORK_ROOT` variable. Extraction, graph generation, traceability validation and artifact upload had already passed. GitHub-hosted runners are ephemeral VMs, so GitHub destroys the runner VM after the job; the explicit `rm -rf` step itself did not succeed. The workflow was corrected to use `$RUNNER_TEMP` directly. Automatic push triggering was removed and the approval contract is now marked consumed, so this one-run authorization cannot launch another extraction accidentally.

## Evidence and gate interpretation

The run artifact is named kmh-graphify-disposable-pilot-<run-id>. Generated graph files are not committed to the repository. If extraction or traceability fails, the workflow uploads any available diagnostic evidence and fails the gate.

## Final acceptance state

| Gate | Result | Evidence |
|---|---|---|
| G0.1 — Official source identity | PASS | Exact v0.9.100 source commit verified |
| G0.2 — License/dependency review | PASS | Apache-2.0 and upstream dependency profile reviewed |
| G0.3 — Known advisory review | PASS | GHSA-pcc4-rvhr-2pr8 review recorded |
| G0.4 — Frozen dependency audit | PASS | PyPI + OSV hash-enforced audit run 41423529714 |
| G0.5 — Single-run owner approval | PASS / CONSUMED | One disposable run, 41430984629 |
| G1 — Scope guard and unit tests | PASS | 36 Creative Studio tests on head 02b65c8 |
| G2 — Disposable extraction | PASS | Graphify v0.9.100 produced 12 nodes and 17 edges |
| G3 — Source traceability | PASS | Six cross-file edges; zero validator errors |
| G4 — Human false-connection review | OPEN | One INFERRED type-annotation edge at outfit_flow.py:L6 |

Production approval remains out of scope.

## Phase 02.3 review handoff

The raw graph artifact is SHA-256 pinned and remains immutable. The source-level review identified one INFERRED `uses` edge at `outfit_flow.py:L6` that duplicates a more precise EXTRACTED `references / parameter_type` edge. Recommendation: HOLD it out of the extracted-only candidate, not classify it as a proven false positive. The 12-node / 16-edge candidate and its hash are recorded in [Phase 02.3](phase-02-3-human-graph-review.md). Project-owner confirmation is still pending.
