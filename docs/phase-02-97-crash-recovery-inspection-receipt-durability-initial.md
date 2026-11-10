# Phase 02.97 — Crash-Recovery Inspection & Receipt Durability (Initial)

**Status:** Non-destructive recovery inspection and atomic JSON receipt replacement committed; CI execution pending.
**Date:** 2026-11-10
**Branch:** phase-02-71/midi-golden-fixtures

## 1. Research basis

RFC 8493 defines BagIt as a filesystem package for opaque payloads and checksum manifests. Its checksums provide strong confidence against accidental corruption but are not designed to defend against active attacks. It requires payload manifest paths to be relative to the bag root and remain within the payload directory; tag manifests must not reference payload files.

Python documents os.fsync() on Unix and Windows. POSIX/Linux durability has an additional directory-entry concern: syncing a file does not necessarily persist the containing directory entry; the directory itself may need to be synced. Atomic rename behavior and directory fsync semantics vary by platform/filesystem.

References:
- https://datatracker.ietf.org/doc/html/rfc8493
- https://docs.python.org/3/library/os.html#os.fsync
- https://man7.org/linux/man-pages/man2/fsync.2.html

## 2. Critical manifest path-base correction

A review of RFC 8493 §2.1.3 found that payload manifest file paths are relative to the bag base directory, not to the data/ directory. The earlier preflight incorrectly used data/ as its resolution base, which could miss symlinks in the actual data/... path.

Corrected validate_manifest_paths():
- resolves all manifest entries from the bag root;
- requires payload manifest entries to begin with data/;
- rejects tag manifest entries beginning with data/;
- checks each actual path component for symlinks;
- retains absolute, drive-letter, backslash, dot/parent and percent-decoded traversal checks.

Added regression tests for valid data/payload.bin, tag-manifest payload references, and a symlink at the real data/link component.

Commits:
- bag-root path-base correction: 54593f386451707fb7d0bbf087e4947c4d37df6d
- manifest path-base and recovery tests: 17dee2ece7b5584509b21c31376ef704f6a61f9f

## 3. Initial crash-recovery inspection

Added inspect_incomplete_ingests(workspace):
- reports reservation files and their readable metadata;
- reports staging directories that may be active or incomplete;
- marks every finding manual_review_required;
- does not delete, move, unlock, or automatically quarantine anything;
- explicitly does not assume a reservation is stale without a liveness check.

Added a regression test confirming that both a reservation and staging directory are reported and left untouched.

## 4. Receipt write hardening

Changed JSON receipt writing to:
- use a unique temporary filename;
- flush and fsync() the temporary file;
- replace the destination atomically where supported;
- best-effort fsync() the parent directory on POSIX.

This is an initial improvement for receipt durability, not a complete crash-consistent transaction. Directory fsync is not implemented as a portable guarantee on Windows, and the BagIt payload/manifests plus accepted-directory promotion still need a complete, platform-specific durability protocol and power-loss tests.

Commits:
- atomic receipt replace + recovery inspector: 2137b0259797aec1b931da84bf925d9871e366a8
- accurate recovery candidate labels: 0b16527bef9c4bbf9b665c8f56f086a8ed889584

## 5. Verification status

- Latest implementation and tests: committed.
- CI for latest commit: not yet observed.
- Last confirmed baseline: Linux Gate A run #53 (13 unit tests and 5 applicable LOC fixtures); this predates Phase 02.95–02.97 changes.
- Windows CI: configured; successful run not yet verified.
- Manifest preflight: still not race-free against hostile concurrent mutation.
- Stale lock ownership/liveness and safe lease recovery: not implemented.
- Full crash-consistent promotion and receipt transaction: not implemented.
- Gate A remains OPEN / NOT CLOSED.

No full RFC conformance, OCFL/PREMIS conformance, independent replica recovery, rights clearance, production readiness or real music ingest is claimed.

## 6. Next actions

1. Run latest Linux and Windows CI and inspect logs/artifacts.
2. Add cross-platform crash-injection tests at each state transition.
3. Define reservation liveness using process identity plus host/boot identity where meaningful; do not delete locks based only on age.
4. Define recovery state machine for staging, accepted promotion, quarantine and receipts.
5. Add durable directory sync strategy per supported OS/filesystem and test actual power-loss/reboot behavior.
6. Add source-mutation race tests and fetch.txt path validation before any fetch-file support.
7. Close Gate A only after evidence passes on supported platforms.