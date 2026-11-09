# Phase 02.98 — Promotion Journal & Accepted-State Recovery

**Status:** Promotion journal, non-destructive journal discovery, and receipt-failure regression test committed; CI execution pending.
**Date:** 2026-11-10
**Branch:** phase-02-71/midi-golden-fixtures

## 1. Research basis

RFC 8493 defines payload manifest paths relative to the bag base directory and requires them to remain within the payload directory. Its security section requires implementations to prevent paths from accessing files outside the bag.

Python documents file fsync and atomic replacement semantics, while Linux fsync documentation explains that syncing a file does not necessarily persist its containing directory entry; directory fsync is needed for that additional durability boundary. These semantics are platform/filesystem dependent and do not by themselves create a multi-file transaction.

PREMIS preservation metadata models Events with identifiers, event type/time, outcome information and links to Objects and Agents. The current journal is an internal recovery record, not yet a PREMIS implementation.

References:
- https://www.rfc-editor.org/rfc/rfc8493.html
- https://docs.python.org/3/library/os.html#os.fsync
- https://man7.org/linux/man-pages/man2/fsync.2.html
- https://www.loc.gov/standards/premis/

## 2. Promotion transaction hardening

Updated ingest promotion sequence:
1. Validate and hash captured payload.
2. Write a promotion-pending journal outside the BagIt root.
3. Rename staging Bag to accepted location.
4. Best-effort sync accepted directory on POSIX.
5. Write final receipt with promotion_status=promoted.
6. Remove journal and best-effort sync reports directory.
7. Release reservation and best-effort sync reservations directory.

If final receipt writing fails after the Bag has been promoted, the worker no longer relabels or moves the accepted Bag into quarantine. It attempts to write an accepted_receipt_pending receipt and retains the promotion journal and reservation for manual reconciliation.

## 3. Recovery inspection

inspect_incomplete_ingests() now also reports *.promotion-pending.json journals as promotion_journal_requires_reconciliation. It remains non-destructive and does not automatically decide that a reservation or staging directory is stale.

## 4. Regression tests

Added tests for:
- final receipt write failure after successful promotion; accepted Bag remains in accepted/;
- accepted_receipt_pending receipt and promotion journal are retained;
- reservation is retained for manual reconciliation;
- recovery inspector discovers promotion journal without deleting it.

Preservation worker test module currently contains 21 named tests. This is a code inspection count, not a test-pass claim.

Commit: ad1029bdda7c2e3262499360dd779a77626a9e1f (latest code/test commit at time of record).

## 5. Verification and limitations

- No CI run for the latest commit has yet been observed.
- Previous full-repository validation run #1897 failed during test discovery because bagit was not installed in that workflow. Dependency installation was added in commit 3ff43e266b13c1808c5839eaa7540574fe2ef0b9; rerun evidence remains pending.
- The current code is not a complete crash-consistent transaction across all filesystems or Windows.
- Process termination at every transition, recovery reconciliation logic, stale-lock liveness, secure race-free path opening, Windows execution, and independent replica recovery remain unverified.
- Gate A remains OPEN / NOT CLOSED.
- No full RFC conformance, PREMIS conformance, OCFL conformance, rights clearance, production readiness, or real music ingest is claimed.

## 6. Next steps

1. Run latest Linux preservation tests and full repository tests after dependency fix.
2. Run Windows preservation tests and inspect artifacts.
3. Add subprocess crash-injection tests at journal write, directory promotion, final receipt, journal deletion, and reservation release.
4. Implement an explicit reconciliation command that validates BagIt payload/manifests before resolving pending journals; never auto-delete evidence.
5. Add host/boot/process liveness model for reservation recovery.
6. Define supported filesystem durability guarantees and test reboot/power-loss behavior.
7. Map accepted/rejected/quarantined/recovered operations into PREMIS Event records only after the event model and provenance requirements are reviewed.