# Phase 02.85 — Gate A Negative-Test Expansion & Security Review

**Status:** FIFO safety improvement and test committed; Gate A CI passed on the updated six-test suite.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures
**Depends on:** Phase 02.84 BagIt Gate A worker.

## 1. Evidence from Phase 02.84

GitHub Actions run #9 first passed the five-test baseline on commit `39f06c16ff2601273ddc0820a7f5d05d8c9c17db`. After adding FIFO nonblocking behavior and a FIFO regression test, Gate A run #13 completed successfully on commit `3f39d5ca7078649a249dd325aff971397685e102`. The `bagit-intake` job and its "Run Gate A tests" step both reported success.

Latest Gate A run:
https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/42659739408

This verifies the six tests present at that commit only. It does not prove the LOC conformance suite or the additional negative cases below.

## 2. Additional security finding: special-file blocking

A FIFO opened with `O_RDONLY` can block before the worker reaches `fstat` and rejects it as non-regular. The worker now adds `O_NONBLOCK` where supported, so opening a FIFO does not wait for a writer and the subsequent file-type check can reject it.

A POSIX-only FIFO test has been added. The updated Gate A workflow completed successfully on the FIFO-test commit.

## 3. Normative security basis

RFC 8493 requires implementations to ensure that paths in payload/tag manifests and fetch files cannot cause access outside the bag directory. It specifically recommends tests for special directory characters and describes path traversal risks. It also states that BagIt checksums are designed for corruption detection, not protection against active attackers; stronger measures such as digital signatures are outside the specification.

References:
- https://www.rfc-editor.org/rfc/rfc8493.html
- https://github.com/LibraryOfCongress/bagit-conformance-suite

The LOC conformance suite has separate v1.0 valid and invalid fixture groups and optional warning and OS-specific groups. Preserve exact fixture bytes; its README warns that Git line-ending conversion can invalidate test bags.

## 4. Required next test matrix

| Test | Expected result |
|---|---|
| Valid synthetic source | accepted; BagIt validates |
| Source symlink | rejected |
| FIFO / named pipe | rejected without blocking |
| Directory/device source | rejected as non-regular |
| Duplicate object ID | rejected without overwrite |
| Object ID traversal | rejected |
| Payload byte modification | BagIt validation fails |
| Missing payload member | BagIt validation fails |
| Unexpected unmanifested payload | BagIt validation fails |
| Corrupt tag manifest | BagIt validation fails |
| Source mutation during capture | rejected or captured immutable snapshot with explicit policy |
| Interrupted write | quarantined; never accepted |
| Malicious manifest path traversal | no access outside bag root |
| Warning fixture | warning surfaced, not silently treated as clean pass |

## 5. Operational and implementation issues to close

- Use an exclusive per-object reservation/lock to prevent concurrent ingests with the same object ID from racing between existence check and final rename.
- Ensure failure receipts are written for early validation failures, not only failures after a staging directory exists.
- Resolve the source and workspace trust boundaries; reject unexpected parent-directory symlink traversal where the platform supports safe descriptor-relative access.
- Capture the actual installed BagIt version using package metadata rather than relying on a module constant that may not exist.
- Include stable run ID, exact commit, dependency artifact hash, OS/filesystem, and validator result in receipts.
- Run the LOC suite separately from the unit tests and retain per-fixture results.
- Treat SHA-256 manifests as fixity evidence, not as authentication or proof of authorship. Add signed receipts or another trusted provenance mechanism only after key custody and verification policy are designed.

## 6. Decision and gate status

- Gate A unit tests: **PASS** for the five-test commit stated above.
- FIFO negative test: **PASS** in Gate A run #13.
- LOC conformance suite: **NOT RUN**.
- OCFL, PREMIS, replica recovery, rights clearance, and production deployment: **NOT STARTED / NOT CLAIMED**.

Do not promote the Verified Music Notes Library to a preservation-ready or production claim based on the current unit-test pass alone.
