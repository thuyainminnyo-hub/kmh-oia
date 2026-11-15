# Phase 02.9S — Source Verification Gate Repair & Independent Revalidation

Status: IMPLEMENTATION CANDIDATE — awaiting CI evidence and owner review.

## Scope and safety boundary

This phase repairs and tests source-identity verification only. It does not install Graphify, execute Graphify, scan the approved corpus, create a graph, rerun Phase 02.9, merge a graph, integrate with OIA runtime, or deploy to production.

The Phase 02.9 failed run remains immutable evidence:
- Run: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/43713763336
- Attempt: 1
- Result: failed before Graphify installation and extraction.
- Its single-run approval is exhausted; no rerun is permitted.

## Defect confirmed in the frozen workflow

The Phase 02.9 workflow uses a regular expression containing a doubled backslash before d. That pattern searches for a literal backslash followed by d, rather than the digit class intended by the author. The official Graphify v0.9.100 source declares _AST_CACHE_SCHEMA = 33.

The repair avoids regular expressions entirely for this check. It parses graphify/cache.py with Python ast and requires exactly one literal top-level assignment. It also parses pyproject.toml with tomllib, checks the package version, verifies the checked-out commit, verifies the annotated release tag resolves to that commit, and verifies the tag's uv.lock blob SHA.

## Frozen source identity under test

- Repository: Graphify-Labs/graphify
- Tag: v0.9.100
- Commit: f5155badddaa3286c78a51653791131e9e2e4d29
- Package: graphifyy 0.9.100
- uv lock blob: 1fd2344a28be6b14c4f6f41c4901c70cadc2be0e
- AST cache schema: 33

## Tests

The tests create temporary synthetic Git repositories and verify:
1. exact commit/tag/lock/version/schema passes;
2. wrong commit fails;
3. tag target mismatch fails;
4. lock blob mismatch fails;
5. package version mismatch fails;
6. missing schema fails closed;
7. duplicate schema assignment fails closed.

No Graphify dependency is installed or invoked by these tests.

## Acceptance criteria

- All source-verifier tests pass in Python 3.12 CI.
- CI is read-only (contents: read).
- The workflow does not install Graphify or invoke extraction.
- Frozen Phase 02.9 approval, trigger, source manifest, and failed-run artifacts remain unchanged.
- No new runtime extraction approval is implied by this PR.
- Owner review is required before any future Phase 02.9 runtime attempt.
