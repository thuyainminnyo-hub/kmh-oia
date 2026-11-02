# Phase 02 — Governed Graphify Integration

**Status:** Guarded preflight scaffold implemented; Graphify installation and indexing are NOT RUN.  
**Release status:** Not approved for production.  
**Target:** A disposable, synthetic-only code fixture inside this Creative Studio module.

## Decision

Graphify is the selected Phase 02 candidate, subject to source/version review and owner approval. The first experiment is deliberately limited to deterministic Python AST extraction from two synthetic files. It must not scan the KMH OIA repository root, MLCW source assets, learner records, private project documents, PDFs, images, audio, or video.

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
- Review the current release, tag/commit, license, dependencies, install scripts, hooks, and permissions at execution time.
- Pin an exact approved package version; the policy intentionally leaves approved_version unset.
- Do not register the assistant skill, install project hooks, or add the project to a global graph during this initial code-only test.
- Do not use .graphifyinclude; current Graphify documentation states that it is no longer supported.

## Operator procedure after approval

Run from a disposable workstation or container with network and filesystem permissions restricted to the approved task.

1. Review the official source and pin the exact package version. Replace no policy values until the technical owner approves the change.
2. Clone or materialize only this feature branch in a disposable workspace.
3. Run the deterministic scope validator and unit tests.
4. Install the reviewed CLI in its isolated tool environment, not into the repository or a global agent configuration.

    uv tool install "graphifyy==APPROVED_VERSION"

5. Build only the synthetic Python graph. Use the documented absolute output-directory override so Graphify writes outside the repository. Keep backend autodetection disabled and run the code-only path.

    GRAPHIFY_OUT=/tmp/kmh-creative-studio-graphify-out GRAPHIFY_BACKEND=none graphify extract "$PWD/case-studies/creative-intelligence-design-studio/graphify-sandbox" --code-only --exclude ".env" --exclude ".env.*" --exclude "**/*.pem" --exclude "**/*.key" --exclude "**/private/**" --exclude "**/learner-data/**" --exclude "**/raw-assets/**" --exclude "**/media/**"

6. Review graph.json and GRAPH_REPORT.md in the external output directory. Confirm that every sampled EXTRACTED edge resolves to a real file and line inside graphify-sandbox/src/.
7. Treat INFERRED or AMBIGUOUS edges as hypotheses. Record them separately and do not promote one to a project fact without independent source evidence and human approval.
8. Record tool version, package/source pin, command, runner details, commit SHA, graph counts, sampled edges, false positives, exclusions, and reviewer decision.
9. Delete the temporary graph output and confirm that it is absent from the repository and workstation after evidence capture.

The output override, backend selector, code-only flag, and repeatable exclude flag are documented in the upstream source:
- https://github.com/Graphify-Labs/graphify/blob/v8/graphify/paths.py
- https://github.com/Graphify-Labs/graphify/blob/v8/graphify/cli.py

The command above is an approved future procedure template only; it has NOT been run in this execution.

## Acceptance gates

**CI evidence (2026-11-02):** Creative Studio QA run [41419384917](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41419384917) passed the design-contract validator, Graphify scope preflight, 14 unit tests, and `git diff --check`. KMH OIA Tests run [41419384909](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41419384909) passed 462 tests and the performance baseline. KMH OIA Validation run [41419385104](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41419385104) passed repository validation, tests, performance evidence, and the deployment evidence bundle.

| Gate | Required evidence | Current state |
|---|---|---|
| G0 — Source and version intake | Official source, license, dependency and version review | PENDING |
| G1 — Scope guard | Validator and unit tests pass in GitHub CI | PASS — Creative Studio QA run 41419384917; 14/14 tests and diff check passed |
| G2 — Isolated code-only extraction | Reproducible graph from synthetic Python fixture | NOT RUN |
| G3 — Source traceability | Sampled EXTRACTED edges resolve to source file/line | NOT RUN |
| G4 — False-connection review | Expected import/call edges present; unsupported links rejected; INFERRED edges separately reviewed | NOT RUN |
| G5 — Owner authorization | Technical owner and data owner approve any scope expansion | PENDING |

## Hard stop conditions

Stop and reject the run if the validator fails, a symlink or unapproved file is present, output includes a sensitive path, any model backend is selected, the scanner targets a path outside graphify-sandbox, or a reviewer cannot resolve an edge to source evidence. Preserve only sanitized QA findings; do not commit generated graph output.

## Relationship to KMH OIA

Phase 02 remains an adapter-level experiment beneath the existing KMH OIA governance boundary. It does not modify the OIA runtime, create a second core, install an agent automatically, or authorize deployment. The current state is a CI-testable preflight scaffold — not a completed Graphify integration and not a production release.
