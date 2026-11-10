# Phase 02.95 — Atomic Object-ID Reservation & Concurrency Regression Test

**Status:** Reservation mechanism and deterministic concurrency test committed; CI execution pending.
**Date:** 2026-11-10
**Branch:** phase-02-71/midi-golden-fixtures

## 1. Research basis

Python documents `os.O_CREAT` and `os.O_EXCL` as available on both Unix and Windows. Creating a reservation file with both flags makes the create operation fail if that name already exists, allowing the worker to claim an object ID before capture begins.

RFC 8493 §5.1 requires BagIt implementations to prevent manifest/fetch paths from accessing files outside the bag, and recommends tests for special directory characters. Windows implementations should test drive-letter and namespace paths as well.

References:
- https://docs.python.org/3/library/os.html
- https://www.rfc-editor.org/rfc/rfc8493.html#section-5.1

## 2. Code change

Updated `scripts/preservation_ingest.py`:
- creates `reservations/<object_id>.lock` with `O_CREAT | O_EXCL | O_WRONLY`;
- writes object ID, process ID and creation timestamp into the reservation record;
- rejects a concurrent claimant with `OBJECT_ID_RESERVED`;
- removes the reservation after successful acceptance or handled ingest failure;
- retains the final duplicate-object check before promotion.

Reservation commits:
- initial atomic reservation: `a4f003ff2a040153a9a497685b8d1227eb233807`
- newline-delimited metadata correction: `daa3b71e2c9cc7a3b74664547ddde34359fc5941`

## 3. Regression test added

Added `test_concurrent_same_object_id_is_atomically_reserved`:
- first ingest is paused deterministically during source capture;
- second ingest attempts the same object ID;
- second request must fail with `OBJECT_ID_RESERVED`;
- first ingest resumes and completes;
- reservation lock must be removed after completion.

Test commit: `1c9bb375570c50b7c0e3cb0c8d774fa8b239519b`.

## 4. Important limitations

- The lock file is a basic atomic reservation, not a complete distributed lock/lease protocol.
- A process crash can leave a stale lock; recovery/lease policy is still required.
- Reservation cleanup on every possible filesystem/report-write failure needs further hardening.
- Path traversal, symlink-parent, source-mutation race and failure-receipt adversarial tests remain outstanding.
- No CI result has yet been observed for these new commits.
- Windows LOC job was added, but its own successful run/artifact has not been verified.
- Linux Gate A run #53 remains the last confirmed passing baseline (13 unit tests and 5 applicable LOC fixtures).

## 5. Next steps

1. Run the new concurrency regression test in Linux and Windows CI.
2. Add crash/stale-lock recovery policy and tests before treating reservation as production-safe.
3. Add RFC 8493 malicious manifest-path tests for POSIX and Windows path forms.
4. Add source mutation race and failure receipt tests.
5. Verify Windows LOC fixture report and retain its artifact.
6. Close Gate A only after cross-platform and adversarial evidence passes.

No full RFC conformance, distributed locking, stale-lock recovery, OCFL/PREMIS integration, independent replica recovery, rights clearance, production deployment or real music ingest is claimed.
