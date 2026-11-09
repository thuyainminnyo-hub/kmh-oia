# Phase 02.84 — BagIt Gate A Worker: First Implementation Record

**Status:** Code committed to working branch; automated execution evidence pending.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures

## Implemented files

- `scripts/preservation_ingest.py` — standalone format-agnostic intake CLI.
- `tests/test_preservation_ingest.py` — synthetic-file preservation, duplicate-ID, invalid-ID, symlink, and missing-source tests.
- `requirements-preservation.txt` — pins `bagit==1.9.0`.
- `.github/workflows/preservation-gate-a.yml` — Python 3.12 CI job for the Gate A test module.

## Worker behavior

- Captures source bytes through an opened file descriptor and computes SHA-256 and byte length while streaming.
- Rejects symlink and non-regular-file sources.
- Copies to a unique staging run directory and independently re-reads the staged copy to compare hash and length.
- Builds a BagIt 1.0 package using SHA-256 from the staged bytes only.
- Validates the bag and independently compares the payload digest/length with intake values.
- Rejects unsafe object IDs and duplicate accepted object IDs.
- Keeps rights status as unknown.
- Writes machine-readable receipts to a separate reports directory.

## Correctness issue found and corrected during review

The first worker draft had two issues:
1. The source subdirectory was not created before opening the staged destination.
2. Writing the intake receipt into the BagIt root after manifest generation would add an unmanifested tag file and invalidate the bag's tag manifest.

Both were corrected:
- Create the destination parent before capture.
- Keep the receipt outside the BagIt package in the reports directory.
- Added a regression assertion that reopens and validates the accepted BagIt package and checks that the receipt is external to the bag.

## Verification status

- Code and test files are committed.
- The GitHub Actions workflow is configured to run the Gate A tests on relevant pull-request and branch changes.
- The GitHub connector returned no workflow runs for test commit `3212889150b69063b7fdb5074c134897f5b8319d` at inspection time.
- Therefore tests are **NOT RUN / NOT VERIFIED** from available evidence. Do not call Gate A passed yet.
- No OCFL, PREMIS, replication, restore, rights clearance, real cultural material ingest, merge, or deployment has occurred.

## Next actions

1. Confirm the new commits trigger the GitHub Actions workflow; inspect run logs and retain artifacts.
2. If CI passes, add negative tests for FIFO/special files, source mutation during capture, corrupted payload, missing payload, unexpected payload, and corrupt tag manifest.
3. Run the Library of Congress BagIt Conformance Suite independently.
4. Only after Gate A passes, begin the OCFL object prototype and PREMIS event mapping.
