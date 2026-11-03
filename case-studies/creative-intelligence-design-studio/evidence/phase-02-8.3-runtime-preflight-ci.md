# Phase 02.8.3 — Runtime Differential Preflight Evidence

Date: 2026-11-03  
Status: **PREFLIGHT CI PASS — RUNTIME EXTRACTION NOT AUTHORIZED**

## Validator coverage gap found and closed

The earlier Phase 02.7 validator scanned only module-level `ImportFrom` statements and considered only top-level function/class scopes. This meant nested function references and function-local imports could be absent from semantic validation even where Graphify had emitted an edge.

The preflight branch changes this:
- collect `ImportFrom` nodes throughout each module;
- attach the import's owning lexical scope;
- inspect nested functions and classes;
- allow function-local imports only within their owner scope and descendants;
- preserve module-level import visibility across module scopes.

Python 3.12 AST documents relative-import `ImportFrom.level`, per-argument `ast.arg.annotation`, function `returns`, and class `bases` as separate AST fields: https://docs.python.org/3.12/library/ast.html

## Runtime pin and isolation contract

The future one-run differential (not invoked in this phase) is locked to:
- Graphify repository/tag: `Graphify-Labs/graphify@v0.9.100`
- source commit: `f5155badddaa3286c78a51653791131e9e2e4d29`
- package: `graphifyy==0.9.100`
- uv: `0.13.6`
- lock blob: `1fd2344a28be6b14c4f6f41c4901c70cadc2be0e`
- Python: `3.12`
- upstream AST cache schema: `33`

The source’s AST cache is version/schema/grammar-fingerprint namespaced; the runtime plan therefore requires a clean disposable working directory, isolated HOME/TMPDIR, and recording the cache path/schema/fingerprint. The planned command uses `--force --code-only --no-dedup --no-cluster --out`; no model credentials or semantic backend are allowed.

The cache contract and CLI flags were inspected at the pinned source:
- `graphify/cache.py` — AST cache namespace `v{version}-s{schema}-g{grammars}`
- `graphify/cli.py` — `--force`, `--code-only`, `--no-dedup`, `--no-cluster`, and `--out` argument handling
- `tests/test_extract_code_only_cli.py` — code-only mode operates without a model key.

## CI evidence

All runs use head commit `746926129ae0f00e91ffd7a90ae979c553daffa1`.

- [Phase 02.8.3 Runtime Differential Preflight CI — run 41554870171](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41554870171) — SUCCESS
  - Phase 02.7 validator tests: 6/6 PASS
  - Phase 02.8.2 differential tests: 9/9 PASS
  - Phase 02.8.3 nested/local-scope tests: 2/2 PASS
  - Runtime preflight contract tests: 6/6 PASS
  - JSON validation, Python compilation and whitespace check: PASS
- [KMH OIA Tests — run 41554870087](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41554870087) — SUCCESS
- [KMH OIA Validation — run 41554870118](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41554870118) — SUCCESS
- [Creative Studio QA — run 41554870000](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41554870000) — SUCCESS

## What these results establish

- The independent validator now covers nested definitions and lexical imports in the synthetic test corpus.
- The runtime pin, lock, cache, command-argument, isolation and approval requirements are recorded as a tested contract.
- No Graphify installation or extraction was performed in Phase 02.8.3.
- No real Graphify runtime differential evidence has been generated yet.

## Governance

- Graphify execution count in Phase 02.8.3: **0**
- New extraction authorization: **PENDING FRESH OWNER APPROVAL**
- Raw Graph and Candidate Graph: unchanged
- G4 Owner HOLD: preserved
- INFERRED/AMBIGUOUS promotion: not authorized
- Global graph merge: not authorized
- OIA runtime integration: not authorized
- Production promotion: not authorized

**Decision:** Phase 02.8.3 preflight and validator-scope correction are CI-verified. Runtime differential is the next gated step, but must remain blocked until a new one-run Owner Approval is recorded against the exact fixture manifest and launch commit.
