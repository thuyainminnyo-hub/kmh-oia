# Phase 02.8.3 — Graphify v0.9.101 Candidate Research

Date: 2026-11-03  
Decision: **SEPARATE CANDIDATE — DO NOT REPLACE v0.9.100 BASELINE**

## Upstream release verification

Official release: https://github.com/Graphify-Labs/graphify/releases/tag/v0.9.101

- Version: `graphifyy==0.9.101`
- Release published: 2026-11-02 19:38:56 UTC
- Annotated tag object: `ab26b1ec1da995743ef5a165a07b0d45ad3314c8`
- Exact source commit: `8e6a6d2129d4aeffc7a0e9ed79b153f7f057f42b`
- `pyproject.toml` blob: `946591be6147204dce8153fa71d6eb91c01d074c`
- `uv.lock` blob: `1fd2344a28be6b14c4f6f41c4901c70cadc2be0e`
- AST cache schema: `36` (v0.9.100 baseline is schema `33`)
- Tag signature: **UNSIGNED**. Pin and verify the exact source commit and repository provenance; do not treat the tag as signed.

## Relevant upstream changes

1. Python PEP 420 namespace imports split across multiple `src/` roots (#4929). The upstream regression suite is `tests/test_src_layout_import_resolution.py`. The regression covers imports across two distributions, inherited method calls, and a free function imported from a sibling distribution. Ambiguous duplicate namespace targets are expected to remain unresolved rather than guessed.
2. Python bare calls inside a method no longer resolve to a same-named method/self-loop (#4933). The upstream regression suite is `tests/test_python_bare_call_not_enclosing_method.py`. Genuine module recursion and explicit `self`/class method calls remain distinct cases.
3. AST cache schema 36 invalidates stale v0.9.100 AST cache entries. The candidate test must use a clean cache and record the grammar fingerprint.

## KMH candidate fixture

Path: `graphify-phase-02-8.3-v09101-candidate/`

- Git tree SHA: `de366efa865172932c4c1ff0d2a60525d1f773af`
- Fixture commit: `f91fd8a6e1f80ab728d9fe9de2140d70d669b9e5`
- Files: 2 Python source files + `.graphifyignore`
- Both distributions have separate `src/` roots.
- Namespace hierarchy deliberately has no `__init__.py`.

Expected runtime relationships (not yet observed):
- cross-src-root import to canonical `DbApiHook`, `free_fn`, and `get_build_status`;
- `PrestoHook` inheritance to the canonical base;
- inherited `strip_sql_string` call;
- imported `free_fn` call;
- bare `get_build_status()` resolves to the imported module function, not a false self-loop to the same-named method.

## Preflight CI

[Run 41556577140](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41556577140) — **SUCCESS**

Test totals:
- Phase 02.7 validator: 6/6
- Phase 02.8.2 synthetic differential: 9/9
- Phase 02.8.3 nested-scope: 2/2
- v0.100 runtime preflight contract: 6/6
- v0.100 frozen scan baseline: 6/6
- v0.9.101 candidate fixture contract: 7/7

Total: **36/36 focused tests PASS**.

The Phase 02.8.3 preflight workflow now pins the two actions it uses to full commit SHAs:
- checkout: `11d5960a326750d5838078e36cf38b85af677262`
- setup-python: `a26af69be951a213d495a4c3e4e4022e16d87065`

## Execution and governance

- Graphify v0.9.101 install: **NOT PERFORMED**
- Graphify extraction: **0**
- Runtime differential: **PENDING FRESH OWNER APPROVAL**
- v0.9.100 baseline: unchanged and immutable
- G4 Owner HOLD: preserved
- INFERRED/AMBIGUOUS promotion: not authorized
- Global merge / OIA integration: not authorized
- Production promotion: not authorized

The candidate is research and fixture evidence only. No claim is made that v0.9.101 runtime behavior has been verified by KMH. The next valid decision is whether to authorize exactly one disposable runtime differential against this frozen candidate fixture, with v0.9.100 retained as the independent baseline comparator.
