# KMH AION OS — Foundation Implementation Plan

## Repository baseline

- Repository: `thuyainminnyo-hub/kmh-oia`
- Default branch at planning time: `main`
- Working branch: `foundation/kmh-aion-os-master-charter`
- Existing runtime: Python, deterministic local execution boundaries
- Existing tests: Python unittest discovery
- Existing security boundary: deterministic tool allowlist
- Existing state: in-memory and local JSON-file implementations
- Existing trace: in-memory tracer

## Baseline evidence reviewed

- `README.md`
- `AGENTS.md`
- `src/main.py`
- `src/agent.py`
- `src/state.py`
- `src/security.py`
- `docs/stage12-production-readiness.md`
- `docs/stage13-security-operations-review.md`

The current README documents the command `python -m src.main "hello"` and test command `python -m unittest discover -s tests -v`. These commands have not been executed in this planning step.

## Implementation decision

The repository already contains an executable KMH OIA runtime and multiple integration boundaries. The foundation work should extend this system, not create a second parallel runtime or prematurely introduce a distributed microservice stack.

## Android-first workflow

1. Open the repository in GitHub mobile web or GitHub Mobile.
2. Work only on the branch `foundation/kmh-aion-os-master-charter`.
3. Review each changed file in the branch diff.
4. Use GitHub Actions or an approved development environment to run tests.
5. Open a pull request to `main` after review; do not merge until checks and owner review pass.

## Next implementation increments

### F1 — Agent and task contract inventory
- Inspect existing agent, workflow, state, event, and schema contracts.
- Identify reusable types and tests.
- Propose the smallest additive agent registry contract.
- Avoid introducing new runtime dependencies.

### F2 — Registry schema and validation
- Add schema-backed agent metadata and task definitions.
- Validate identity uniqueness, allowed status values, and capability declarations.
- Add negative tests for malformed and unauthorized records.

### F3 — Persistent, scoped memory
- Reuse existing memory boundaries where possible.
- Add explicit visibility and provenance metadata.
- Keep untrusted content quarantined until reviewed.

### F4 — Security and audit
- Extend authorization only after reviewing all current call sites.
- Add structured security decision events.
- Test denial, approval, and revocation paths.

## Verification protocol

For each increment report:
- exact files changed
- exact commands run
- PASS / FAIL / BLOCKED / NOT RUN
- CI run URL and commit SHA, if available
- known limitations and rollback path

No test result or production status may be inferred from a successful GitHub write.
