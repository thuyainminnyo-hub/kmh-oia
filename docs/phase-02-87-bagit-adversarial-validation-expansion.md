# Phase 02.87 — BagIt Adversarial Validation Expansion

**Status:** Adversarial unit tests committed; CI and LOC conformance evidence pending.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures
**Depends on:** Phase 02.84–02.86.

## 1. Research findings

The Library of Congress BagIt Conformance Suite is a fixture corpus, not merely another unit-test library. Its layout is grouped by BagIt RFC version and includes:
- `valid`: bags expected to validate successfully;
- `invalid`: bags expected to fail validation;
- optional `warning`: bags that remain valid but should produce a warning;
- optional OS-specific groups such as `linux-only` and `windows-only`.

The supplied test harness runs a validator CLI using conventional exit codes (0 for valid, non-zero for invalid) and reports warning stderr. It recommends disabling Git line-ending conversion (`core.autocrlf=false`) because CRLF conversion can invalidate fixture bytes.

Source: https://github.com/LibraryOfCongress/bagit-conformance-suite

RFC 8493 requires support for SHA-256 and SHA-512 starting with BagIt 1.0 and recommends SHA-512 by default. It requires every payload file to appear in every payload manifest and requires all payload and tag checksums to validate. It also requires path handling to prevent access outside the bag directory and recommends special-character security tests.

Source: https://www.rfc-editor.org/rfc/rfc8493.html

## 2. New adversarial unit tests

Added tests for:
- payload byte tampering;
- missing payload member;
- unexpected/unmanifested payload member;
- corrupted SHA-512 tag manifest.

The corrupt-tag fixture was reviewed to ensure it contains an actual newline-terminated manifest entry rather than a literal backslash-n sequence.

These tests use the pinned bagit-python validator against deliberately modified local test bags. They are useful unit tests, but are not substitutes for the LOC fixture corpus.

## 3. Verification status

- Previous six-test suite passed in Gate A run #13 on commit `3f39d5ca7078649a249dd325aff971397685e102`.
- Dual SHA-256/SHA-512 worker changes and regression assertions were committed in Phase 02.86; new CI result was not confirmed at that time.
- Adversarial tests committed in Phase 02.87; CI run for the new commit is pending/not observed.
- LOC conformance suite has not yet been run.
- No claim of full Gate A completion, OCFL/PREMIS conformance, replica recovery, rights clearance, or production readiness.

## 4. Next execution plan

1. Confirm GitHub Actions passes the expanded unit suite on the latest commit.
2. Add an isolated CI job to checkout the LOC conformance suite with line-ending conversion disabled.
3. Build a small CLI adapter for bagit-python only if needed; retain each fixture's expected category and actual exit code/stderr.
4. Preserve per-fixture JSON results and summarize valid/invalid/warning/OS-specific outcomes.
5. Add malicious manifest path traversal tests and concurrency/source-mutation tests to the worker itself.
6. Do not treat warning fixtures as clean passes without recording the warning.

## 5. Gate policy

Gate A is eligible for closure only after both:
- worker-specific unit/security tests pass; and
- the LOC independent conformance corpus produces expected results with machine-readable per-fixture evidence.

No standards-compliance or production claim may be made before both evidence sets are retained.
