# Phase 02.7 — Cross-file Resolution Compatibility Matrix

**Owner authorization:** Explicitly granted in conversation on 2026-11-02 for one fresh disposable extraction.  
**Execution state:** Preparation code and isolated fixtures committed; a separate one-run approval and dedicated launch branch will control the GitHub-hosted extraction.  
**Graphify:** v0.9.100, exact source commit and frozen `uv.lock` pin from the reviewed intake.  
**Production:** Not authorized.

## 1. Scope

Phase 02.7 expands the existing two-file synthetic pilot to a ten-file Python-only fixture matrix:
- Original `contract_guard.py` and `outfit_flow.py` remain unchanged.
- Package alpha and beta each define a class named `Widget`, so exact module-based disambiguation is observable.
- Relative imports, aliases, absolute multi-package imports, type annotations, imported function calls, single inheritance and multiple inheritance are included.
- No real KMH OIA application code, child/learner data, private documents, images, media, credentials or source assets are in scope.

The existing `graphify-scope-policy.json` remains `preflight_only`. Phase 02.7 execution authority is a separate one-run contract; it does not widen future default permissions.

## 2. Compatibility matrix

| Area | Synthetic source case | Expected observation |
|---|---|---|
| Relative package import | `pkg_alpha/service.py` → `.types` | Exact source module resolved |
| Alias import | `Widget as AlphaWidget` | Canonical target remains alpha `Widget` |
| Same-name definitions | alpha `Widget` vs beta `Widget` | Distinct source-backed canonical IDs |
| Type reference | `build_alpha(value: AlphaWidget)` | `references / EXTRACTED` |
| Imported function call | `normalize_alpha(value)` | `calls / EXTRACTED` |
| Single inheritance | `AlphaChild(AlphaBase, AlphaMixin)` | Two canonical `inherits` links |
| Absolute multi-package import | `integration.py` imports both package modules | Each alias resolves to correct package |
| Multi-package inheritance | `CombinedWidget(AlphaBase, BetaBase)` | Both parent IDs remain distinct |
| Candidate separation | Raw graph vs EXTRACTED-only candidate | Candidate contains no INFERRED/AMBIGUOUS edges |

## 3. One-run execution boundary

The separate owner approval will authorize exactly one Graphify v0.9.100 code-only extraction:
- GitHub-hosted `ubuntu-24.04` ephemeral runner only.
- Clone and verify official source commit and exact `uv.lock` blob.
- `uv 0.13.6`, `uv sync --frozen --no-dev --python 3.12`; no optional extras.
- Copy exactly the ten approved Python files plus `.graphifyignore` to a new external `RUNNER_TEMP` scan snapshot.
- Read-only scan snapshot; SHA-256 source manifest; no symlinks.
- Run `graphify extract --code-only --no-dedup --no-cluster` using a clean environment with no model credentials.
- Write graph output outside the scan root.
- Upload raw graph, EXTRACTED-only candidate, source manifest and QA reports as 14-day artifacts.
- Delete temporary workspaces in an `if: always()` cleanup step.
- No assistant Skill, Git hook, MCP, global graph merge, OIA runtime integration, or production deployment.

The exact trigger marker and approval contract are distinct from the already-consumed Phase 02.2 approval. The workflow refuses any second attempt.

## 4. Validator contract

`scripts/validate_phase_02_7_graph.py` independently validates:
- Exact source file set, safe path confinement, no symlinks, AST parseability and source line bounds.
- Node ID uniqueness and complete edge endpoint resolution.
- Every source declaration maps to one source-backed graph node.
- Imported symbol references resolve to the unique definition in the exact package module.
- Canonical edge target IDs agree with imported definition file and line.
- Relative imports, aliases, absolute imports, same-named types, calls and inheritance.
- Full coverage matrix from the versioned baseline.
- Raw graph remains unchanged; candidate is a separate deep copy containing only EXTRACTED edges.
- INFERRED/AMBIGUOUS edges are preserved in raw review evidence and excluded from the candidate.

This is a source-to-graph compatibility QA, not a production-quality benchmark and not proof that every Python packaging/import pattern is supported.

## 5. Residual upstream risk

Graphify v0.9.100 was released on 2026-11-01. Its release notes include cross-language JVM import, inheritance and member-call resolution improvements. Upstream Issue #1186 remains open for remaining language-specific cross-file cases, while its original report targeted v0.8.35. Upstream Issue #4182 on dangling raw no-cluster endpoints was closed by fix #4183 before the pinned v0.9.100 release. Phase 02.7 explicitly checks all raw edge endpoints and fails if any remain unresolved.

References:
- [Graphify v0.9.100 release](https://github.com/Graphify-Labs/graphify/releases/tag/v0.9.100)
- [Issue #1186](https://github.com/Graphify-Labs/graphify/issues/1186)
- [Issue #4182 and fix #4183](https://github.com/Graphify-Labs/graphify/issues/4182)
- [Headless extraction guide](https://github.com/Graphify-Labs/docs/blob/main/guides/headless-extraction.mdx)

## 6. Current status

- Owner authorization for one bounded extraction: GRANTED by user instruction.
- Approval contract: to be recorded in separate launch commit.
- Source fixtures: prepared.
- Validator and regression tests: prepared.
- Raw/candidate Phase 02.5 artifacts: unchanged.
- Graphify execution: not yet performed by this preparation commit.
- Production promotion / OIA runtime integration: NOT AUTHORIZED.
