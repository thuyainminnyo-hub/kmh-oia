# Phase 02.94 — Windows Conformance Job & Cross-Platform Declaration Tests

**Status:** Windows job added; execution evidence pending.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures

## 1. Research basis

GitHub-hosted Windows Server 2025 is a supported Actions runner label (`windows-2025`). Current runner-image documentation lists it as an x64 Windows runner. Python's `os.open` flags have platform-specific availability: `O_EXCL` is available on Windows and Unix, while flags such as `O_NOFOLLOW` and `O_NONBLOCK` are not universally available. The worker uses `getattr(os, flag, 0)` for optional flags, but actual worker behavior still needs Windows tests.

References:
- https://github.com/actions/runner-images/blob/main/README.md
- https://docs.python.org/3/library/os.html
- https://datatracker.ietf.org/doc/html/rfc8493#section-5.1

## 2. Changes committed

- Added a dedicated `bagit-windows-conformance` job using `runs-on: windows-2025`.
- The job checks out the same pinned LOC BagIt Conformance Suite commit `9ab48705c06664f9f419ca740c728c9f89a61e7c`.
- It installs the pinned BagIt dependency, runs strict declaration tests, executes the conformance runner, and uploads a separate Windows JSON evidence artifact.
- Added tests for CRLF declaration line endings and UTF-8 BOM rejection, in addition to valid syntax, malformed whitespace, and line-count tests.

Commits:
- Windows CI job: `8a319e81113e32aa1a3467c7073cb3ab0fb9f83b`
- CRLF/BOM test additions: `487952e81aae90889ded92afcd30f599042c03f7`
- Byte fixture correction: `177c14360f3ef97545993245f72acdd5e0c3e545`

## 3. Verification state

- Linux Gate A run #53: PASS (13 tests, 5 LOC fixtures).
- Windows job: committed; no successful Windows execution evidence observed yet.
- CRLF and BOM tests: committed; new CI result pending.
- Worker-specific Windows behavior: not yet tested.
- Gate A: OPEN / NOT CLOSED.

## 4. Next execution steps

1. Confirm the Windows job is triggered and reaches completion.
2. Review Windows fixture report and preserve its artifact.
3. Add worker tests for concurrent object-ID reservation; the current check-then-`os.replace` sequence is not an atomic reservation and can race under concurrent ingests.
4. Add path traversal and symlink-parent tests; RFC 8493 §5.1 requires paths in manifests/fetch files not to access outside the bag.
5. Add source-mutation race coverage and verify failure receipts.
6. Close Gate A only after supported-platform tests pass.

No Windows pass, atomic reservation, full RFC conformance, OCFL/PREMIS conformance, independent recovery, rights clearance, or production readiness is claimed.
