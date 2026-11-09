# Phase 02.97 Addendum — Full Repository CI Dependency Fix

**Status:** Dependency fix committed; rerun pending.

## CI evidence

GitHub Actions KMH OIA Validation run #1897: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/42667886818

- performance-evidence job: PASS.
- tests job: FAIL during unittest discovery because `tests/test_preservation_ingest.py` could not import `bagit` (`ModuleNotFoundError`).
- This is a CI environment dependency-installation gap; the full test run did not reach preservation test execution.

## Correction

Updated `.github/workflows/validation.yml` to install `requirements-preservation.txt` before unittest discovery in both the `tests` and `repository-validation` jobs.

Commit: `3ff43e266b13c1808c5839eaa7540574fe2ef0b9`.

Latest workflow rerun for this correction has not yet been observed. Do not treat it as fixed until the full CI jobs pass.

## Current preservation status

- RFC 8493 payload manifest base corrected to bag-root-relative `data/...` paths.
- Adversarial path tests and non-destructive recovery inspection tests committed.
- Atomic JSON receipt replacement and best-effort POSIX parent-directory fsync committed.
- Crash-consistent BagIt promotion, stale reservation liveness/recovery, Windows verification, and race-free path opening remain incomplete.
- Gate A remains OPEN / NOT CLOSED.