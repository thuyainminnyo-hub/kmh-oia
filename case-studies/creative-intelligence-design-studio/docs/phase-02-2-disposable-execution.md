# Phase 02.2 — Graphify Disposable Execution

Approval: Project-owner approval recorded 2026-11-02 for one disposable GitHub-hosted synthetic run.
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
8. Upload the graph and sanitized traceability report for 14 days, then delete the temporary workspace.

## Traceability acceptance checks

- The graph JSON contains node and edge arrays.
- Node IDs are unique and every edge endpoint resolves.
- Source-backed nodes and edges refer only to the two approved source files.
- Every source-backed node and edge line reference exists within the actual source file.
- Required symbols appear in the correct source files: DesignToken, is_approved_token and select_outfit.
- At least one cross-file edge connects the two fixtures.
- Confidence labels are restricted to EXTRACTED, INFERRED and AMBIGUOUS.
- INFERRED and AMBIGUOUS edges are reported for human review and never automatically promoted to facts.

## Evidence and gate interpretation

The run artifact is named kmh-graphify-disposable-pilot-<run-id>. Generated graph files are not committed to the repository. If extraction or traceability fails, the workflow uploads any available diagnostic evidence and fails the gate.

G0.1–G0.5 and G1 are complete. G2 and G3 remain pending until the workflow finishes. G4 (manual review of false connections and inferred/ambiguous links) remains a separate human QA decision. Production approval remains out of scope.
