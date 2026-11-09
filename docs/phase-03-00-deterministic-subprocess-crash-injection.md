# Phase 03.00 — Deterministic Subprocess Crash Injection

**Status:** Test seam and eight checkpoint crash test committed; CI runs pending.
**Date:** 2026-11-10
**Branch:** `phase-02-71/midi-golden-fixtures`

## Research basis

USENIX OSDI 2018 research on bounded black-box crash testing (B3) demonstrates that crash consistency must be checked by exploring crash points and validating recovered persistent states, rather than relying only on normal execution or exception paths. CrashMonkey/Ace record workloads, simulate crash states, and compare recovered filesystem state against consistency expectations.

2026 research also includes MC3, a model-checking approach targeting full-stack filesystem crash consistency. It reinforces that application-level fault injection is useful but cannot prove lower-level filesystem/power-loss behavior.

References:
- https://www.usenix.org/conference/osdi18/presentation/mohan
- https://github.com/utsaslab/crashmonkey
- https://ieeexplore.ieee.org/abstract/document/11645445/

## Implementation

Added an optional `crash_hook` argument to `ingest()`. It is inert by default and exposes named checkpoints only when explicitly supplied by tests:
- `reservation_durable`
- `source_captured`
- `bag_validated`
- `journal_durable`
- `promotion_durable`
- `receipt_durable`
- `journal_removed`
- `reservation_released`

Added a subprocess regression test that calls `os._exit(91)` at each checkpoint. Since `os._exit` terminates the child without executing Python cleanup handlers, this tests abrupt process termination and persistent on-disk state, not just a caught exception.

Post-crash assertions inspect accepted Bag existence, journal and receipt presence, reservation state, BagIt validity, and payload byte equality with the original fixture.

Commit: `60d6f3f74f97e53e1867044042f00fadb492c045`.

## Verification state

- The code and test were fetched back from GitHub and all eight checkpoint names were confirmed present.
- GitHub Actions runs for this commit were queued at inspection time: Tests `42719154759`, Validation `42719154811`, Preservation Gate A `42719154822`, MIDI Fixture Integrity `42719154735`; earlier runs on the same commit were also in progress.
- Do not claim the new subprocess crash test passed until these exact-commit runs complete and logs are inspected.
- `os._exit` tests process termination, not power-loss, kernel crash, block-device write reordering, torn writes, or physical storage durability.
- Windows/Linux CI success for the prior Gate A commit does not automatically apply to this new crash-injection commit.
- Gate A remains OPEN / NOT CLOSED; PR #217 remains OPEN / DRAFT.

## Next steps

1. Inspect all exact-commit CI results and crash-test logs.
2. Add explicit recovery planner validation for every crash state; current inspector only reports candidates and does not reconcile them.
3. Test failures at individual write/fsync/rename/unlink operations, including torn or partial receipt writes.
4. Add VM/block-device crash testing on supported Linux filesystems if stronger power-loss claims are needed.
5. Define platform-specific durability guarantees and keep Windows results separate from POSIX directory-fsync claims.
6. Do not close Gate A until all required recovery invariants are verified.