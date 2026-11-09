# Phase 02.93 — Gate A Unit & LOC Conformance Pass (Linux)

**Status:** CI PASS for current Linux-applicable Gate A scope; full Gate A remains open pending Windows and remaining worker security cases.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures

## 1. Confirmed GitHub Actions evidence

Preservation Gate A run #53 completed successfully.

- Gate A unit tests: 13/13 PASS.
  - 10 preservation worker tests.
  - 3 strict BagIt declaration tests.
- LOC BagIt v1.0 fixtures: 5/5 PASS on Linux.
- JSON conformance report uploaded successfully.
- Overall job: SUCCESS.

Run:
https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/42662890020

Artifact:
https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/42662890020/artifacts/13695322668

Tested commit: `a44087514808443dcdc2dfe85d26a6f743c8f835`.
Pinned LOC suite commit: `9ab48705c06664f9f419ca740c728c9f89a61e7c`.
Validator: bagit-python 1.9.0.
Platform: Linux, Python 3.12.

## 2. Per-fixture outcome

| Fixture | Category | Raw bagit-python | Strict declaration | Expected | Result |
|---|---|---:|---:|---|---|
| basicBag | valid | valid | valid | valid | PASS |
| bagit-with-invalid-whitespace | invalid | valid | invalid | invalid | PASS |
| notAllManifestsListAllFiles | invalid | invalid | valid | invalid | PASS |
| same-filename-listed-twice-with-different-hashes | invalid | invalid | invalid | invalid | PASS |
| same-filename-listed-twice-with-the-same-hash | invalid | invalid | valid | invalid | PASS |

The malformed whitespace fixture demonstrates why KMH retains both the raw validator result and the supplementary RFC 8493 declaration result: bagit-python 1.9.0 alone accepts a declaration that the LOC corpus expects to fail.

## 3. Scope limits

This is a successful Linux run of the fixtures present in the pinned v1.0 suite snapshot, not a claim that all BagIt implementations or platforms are conformant.

- Windows-only fixtures are not exercised on Linux.
- The pinned suite snapshot contains five applicable fixture directories for this runner.
- The runner's strict supplement currently validates the two-line BagIt declaration, not every RFC requirement independently.
- No claim of full Gate A closure, OCFL/PREMIS conformance, replica recovery, rights clearance, or production readiness.

## 4. Next security gate

Proceed with:
1. Windows CI job for Windows-specific invalid fixtures.
2. Atomic object-ID reservation to prevent concurrent duplicate ingests.
3. Path traversal and symlink-parent defenses.
4. Source mutation/race tests.
5. Failure receipts for early validation failures.

Only after these tests pass on supported platforms should Gate A be considered closed.
