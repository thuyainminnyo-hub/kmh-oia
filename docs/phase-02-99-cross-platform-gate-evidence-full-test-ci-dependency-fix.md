# Phase 02.99 — Cross-Platform Gate Evidence & Full-Test Workflow Dependency Correction

**Status:** Linux and Windows Preservation Gate A PASS on commit `a10a227de21eeb241a852ce0d7e18ba98322e9b1`; dedicated full-test workflow dependency fix committed; rerun queued.
**Date:** 2026-11-10

## 1. Verified CI evidence

Commit: `a10a227de21eeb241a852ce0d7e18ba98322e9b1`.

GitHub Actions run IDs:
- KMH Preservation Gate A: `42668964957` — workflow completed successfully.
- KMH MIDI Fixture Integrity: `42668965040` — success.
- KMH OIA Validation: `42668964635` — success.
- KMH OIA Tests: `42668964429` — failure.

Preservation Gate A job-level evidence:
- Linux `bagit-intake`: PASS; 26 unit tests (21 preservation worker tests + 5 strict declaration tests); LOC conformance fixtures: 5 passed, 0 failed.
- Windows `bagit-windows-conformance`: PASS; 26 unit tests; LOC conformance fixtures: 5 passed, 0 failed.
- Both evidence artifacts uploaded and not expired at inspection time: `bagit-conformance-evidence` and `bagit-conformance-evidence-windows`.

These results establish the configured Gate A tests and the five pinned LOC fixtures on Linux and Windows for this exact commit. They do not establish full RFC 8493 conformance or production readiness.

## 2. Separate full-test workflow failure

KMH OIA Tests run `42668964429` failed because `.github/workflows/test.yml` did not install `requirements-preservation.txt` before `python -m unittest discover -s tests -v`. The log shows `ModuleNotFoundError: No module named 'bagit'` during test-module import. The test suite therefore did not fully execute.

Correction committed:
- `.github/workflows/test.yml` now installs `requirements-preservation.txt` before unittest discovery.
- Commit: `03c089bb956e3ee26f0236c12b9eb11bd464e491`.
- Workflows for this commit were queued at inspection time: `42718801890` (KMH OIA Tests), `42718801865` (Preservation Gate A), `42718801879` (Validation), and `42718802231` (MIDI Fixture Integrity).
- Their final conclusions are pending; do not claim the dependency correction has passed until completed runs are inspected.

## 3. Scope and interpretation

- The dedicated Preservation Gate A is now verified on both Linux and Windows for commit `a10a227...`.
- The full repository test workflow remains unresolved until the queued run for `03c089...` completes.
- The Phase 02.98 promotion-journal behavior has a passing targeted regression test on both operating systems as part of the 26-test Gate A job.
- No deterministic subprocess kill-at-every-transition test exists yet. The current receipt-failure test simulates a write exception; it is not equivalent to killing the process or power loss.
- No automated journal reconciliation, stale-lock liveness protocol, race-free hostile-tree path opening, independent replica recovery, PREMIS/OCFL conformance, rights clearance, or production readiness is claimed.
- PR #217 remains OPEN / DRAFT.

## 4. Next execution steps

1. Inspect queued workflows for commit `03c089...`; resolve any actual test failures, not only dependency setup.
2. Add subprocess crash injection at journal write, rename/promotion, final receipt, journal removal, and reservation release.
3. Implement a read-only recovery planner that validates BagIt and hashes before proposing a reconciliation action; require explicit operator approval before mutation.
4. Add stale-lock liveness evidence using process/host/boot identity; never expire locks solely by age.
5. Add source-mutation race tests and stronger path-open protections against concurrent staging-tree mutation.
6. Retain and periodically revalidate Linux/Windows conformance artifacts.
7. Keep Gate A open until full required CI and recovery evidence is reviewed.