# Phase 02.90 — Gate A Failure Root-Cause Analysis & Regression Corrections

**Status:** Test defects corrected in code; rerun CI pending.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures

## 1. Observed CI failure

GitHub Actions Preservation Gate A run #37 executed the expanded ten-test suite and reported:
- `test_missing_payload_detected`: ERROR (FileNotFoundError)
- `test_corrupt_tag_manifest_detected`: FAIL (BagValidationError not raised)
- remaining eight tests: PASS

Run: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/42662344132

## 2. Root cause analysis

### Missing payload test
The test helper creates a directory containing a pre-existing `data/` folder and then calls `bagit.make_bag()`. bagit-python performs a bag-in-place operation: it moves the original directory contents under a newly created `data/` directory. Therefore the actual payload path becomes `data/data/payload.bin`, not `data/payload.bin`.

Correction: remove the payload at the actual nested path before calling validate.

### Corrupt tag manifest test
The test modified the tag manifest on disk but called `validate()` on the already-instantiated `Bag` object. bagit-python loads manifests during `Bag()` construction, so the object retained the pre-tamper manifest entries in memory.

Correction: instantiate a fresh `bagit.Bag(bag.path)` after modifying the tag manifest, then validate the reloaded object.

The source implementation confirms `make_bag()` moves the existing directory contents into a newly created `data/` directory, and `Bag._open()` loads manifests during object construction.

## 3. Code correction commits

- Missing payload path correction: `3815e1b83994b86aa56e16eaa52777655bb8bccd`
- Tag-manifest reload correction: `67941c8e73f993b63eb30d6c5c3c32e978414f4b`

## 4. Verification status

- Run #37: FAIL; this is retained as a real regression finding.
- Both test defects corrected in the working branch.
- CI for correction commit `67941c8e73f993b63eb30d6c5c3c32e978414f4b`: not yet observed.
- LOC conformance step was skipped in run #37 because the unit-test step failed.
- No independent conformance report or artifact exists yet.
- Gate A remains OPEN / NOT PASSED.

## 5. Next actions

1. Confirm the corrected ten-test suite passes in a new CI run.
2. Ensure the LOC conformance step executes after unit tests pass and retain its JSON artifact.
3. Review every fixture result; verify Linux-only invalid fixtures fail as expected.
4. Add Windows runner coverage for Windows-only invalid fixtures.
5. Continue with path traversal, concurrent object-ID reservation, and source-mutation tests.

No OCFL/PREMIS conformance, independent replica recovery, rights clearance, production deployment, or real music ingest is claimed.
