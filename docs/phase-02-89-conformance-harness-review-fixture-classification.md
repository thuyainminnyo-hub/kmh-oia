# Phase 02.89 — Conformance Harness Review & Fixture Classification Fix

**Status:** Harness review corrections committed; CI execution pending.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures

## 1. Official research confirmation

The bagit-python README explicitly documents `python -m bagit --help` and `python -m bagit --validate <bag-path>` as supported command-line usage. The LOC suite therefore can use the pinned Python module CLI without relying on an undocumented script path.

References:
- https://github.com/LibraryOfCongress/bagit-python
- https://github.com/LibraryOfCongress/bagit-conformance-suite

RFC 8493 section 5.1 specifically warns that malicious manifest paths such as absolute paths, `..`, and home-directory references must not cause access outside the bag. It recommends tests for special directory characters and points to the LOC suite's POSIX/Windows invalid cases. It also states that BagIt checksums are not authentication against active attacks.

Reference:
- https://datatracker.ietf.org/doc/html/rfc8493#section-5.1

## 2. Harness review corrections

Review of the Phase 02.88 runner found two correctness points:

1. The `linux-only` and `windows-only` fixture groups are platform-specific invalid cases, not generic warning fixtures. They must be expected to fail validation on their matching operating system.
2. The validator was invoked with `--quiet`, which could suppress warning output. The runner now captures normal validator output so warning evidence is not hidden.
3. The runner now fails closed if no v1.0 fixture directories are discovered, preventing a zero-fixture run from looking like a successful conformance pass.

The runner continues to:
- use `python -m bagit --validate`;
- preserve per-fixture exit code, stdout, stderr and category;
- record suite commit, validator version, OS, Python version and timestamp;
- skip OS-specific groups that do not match the current platform.

## 3. Code commit

Harness correction commit:
`e4b59925d4a8e0f76d99e68eb974ff69e3e19425`

## 4. Verification status

- LOC suite source pinned in workflow: `9ab48705c06664f9f419ca740c728c9f89a61e7c`.
- Harness corrections: committed.
- CI run for corrected harness: not yet observed.
- Per-fixture JSON report: not yet generated.
- Independent conformance: NOT VERIFIED.
- Gate A: NOT CLOSED.

## 5. Next execution

1. Confirm CI executes the corrected runner.
2. Inspect valid, invalid and Linux-only fixture outcomes.
3. Retain all stdout/stderr and review warning fixture behavior.
4. Add Windows CI to cover Windows-only fixtures.
5. Implement dedicated path traversal and concurrent object-ID race tests for the KMH worker.
6. Close Gate A only after both worker-specific security tests and independent conformance have passed with retained evidence.

No OCFL/PREMIS integration, independent replica recovery, rights clearance, production deployment or real music ingest is claimed.
