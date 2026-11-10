# Phase 02.96 — BagIt Manifest Path Containment & Symlink Preflight

**Status:** Defensive preflight and adversarial tests committed; CI execution pending.
**Date:** 2026-11-10
**Branch:** phase-02-71/midi-golden-fixtures

## 1. Official specification findings

RFC 8493 §5.1 states that implementations MUST ensure paths in payload manifests, tag manifests and fetch files do not access files outside the bag. It specifically identifies absolute paths, `..`, home-directory references, Windows drive letters and namespace paths as attack surfaces, and recommends a dedicated test suite.

RFC 8493 also specifies that manifest file paths are relative to the payload or bag base as appropriate, use forward slash separators, and encode LF, CR, CRLF and percent characters according to URI percent-encoding rules.

References:
- https://datatracker.ietf.org/doc/html/rfc8493#section-5.1
- https://www.rfc-editor.org/rfc/rfc8493.html
- https://docs.python.org/3/library/os.html

Python documents that `dir_fd` support is platform-dependent and currently Unix-only; it cannot be the sole cross-platform defence when Windows is a supported target. Windows also has path/reparse-point semantics that require dedicated tests.

## 2. Implementation committed

Added `validate_manifest_paths()` to `scripts/preservation_ingest.py` and invoke it before `bag.validate()`.

The preflight:
- uses `data/` as the base for payload manifests and the bag root for tag manifests;
- decodes RFC-style percent-encoded path characters before security checks;
- rejects empty, absolute, home-relative, drive-letter, backslash, dot and parent components;
- checks each existing path component for symlinks;
- confirms resolved candidates remain beneath their correct base directory;
- rejects symlink manifest files.

The preflight docstring explicitly states that this is not race-free against a hostile process that can mutate the staging tree concurrently. Descriptor-relative/race-free opening remains a separate hardening task.

## 3. Adversarial tests added

Added tests for:
- POSIX parent traversal (`../`);
- absolute paths;
- Windows drive-letter paths;
- symlink parent escape;
- percent-encoded parent traversal.

Also corrected path-base handling and preserved literal leading asterisks in filenames.

The Windows CI job now runs the preservation worker test module as well as the strict declaration test module before running the pinned LOC fixtures.

Commits:
- initial preflight: `1b9769832fd85c723c627c3a8ae8a594eb3278ea`
- correct payload/tag base and percent-decoding: `549559c8b10b49dae96831384b3a07ff38f4803c`
- adversarial tests: `327799c3ab892c76b29036d9d24f176c034e6cce`
- test newline correction: `96eb5dd102eee7b67b609334af02906421571308`
- literal asterisk handling: `53e3070723222c505d909338d10a274af8233bf8`
- run worker tests on Windows: `ad70a37225bb0238ec713720a34fd1f891579f77`

## 4. Verification status

- Code and tests: committed.
- CI for current head: no run observed yet.
- Last confirmed Linux baseline: Gate A run #53 (13 tests and 5 Linux-applicable LOC fixtures).
- Windows runner: job exists; Windows result not yet verified.
- Path preflight is not a complete race-free filesystem security boundary.
- Fetch-file path coverage, Windows namespace/device-name edge cases, source mutation race and stale reservation recovery remain.

Gate A remains OPEN / NOT CLOSED. No full RFC conformance, OCFL/PREMIS conformance, independent recovery, rights clearance, production readiness or real music ingest is claimed.

## 5. Next steps

1. Verify the new Linux and Windows jobs execute on the latest commit.
2. Review all adversarial test outcomes and JSON conformance artifacts.
3. Add tests for Windows namespace paths and encoded separator edge cases.
4. Design a platform-specific secure open strategy for hostile writable roots; do not claim race-free protection from the current preflight.
5. Add stale reservation recovery and crash-injection tests.
6. Add source-mutation race tests and verify every early failure leaves an auditable receipt.
