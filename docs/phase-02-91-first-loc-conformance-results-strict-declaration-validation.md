# Phase 02.91 — First LOC Conformance Results & Strict Declaration Validation

**Status:** Gate A unit tests passed; LOC conformance found one validator/spec mismatch; strict RFC check added, rerun pending.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures

## 1. Confirmed GitHub Actions evidence

Preservation Gate A run #41 completed with overall failure:
- Gate A unit tests: PASS — 10 tests.
- LOC conformance: 4 of 5 fixtures passed; 1 failed.
- JSON artifact uploaded successfully.

Run:
https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/42662507265

Artifact:
https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/42662507265/artifacts/13694831904

Pinned suite commit: `9ab48705c06664f9f419ca740c728c9f89a61e7c`.
Validator: bagit-python 1.9.0.
Platform: Linux, Python 3.12.16.

## 2. Failed fixture and root cause

The only failed fixture was:
`v1.0/invalid/bagit-with-invalid-whitespace`

Its `bagit.txt` contains:
- `BagIt-Version : 1.0`
- `Tag-File-Character-Encoding : UTF-8`

RFC 8493 §2.1.1 requires the bag declaration to consist of exactly two lines in the form `BagIt-Version: M.N` and `Tag-File-Character-Encoding: ENCODING`. The bagit-python 1.9.0 CLI accepted this whitespace-before-colon form and returned success, while the LOC fixture correctly expects invalid.

This is a validator/spec strictness mismatch, not a payload checksum failure.

Reference:
https://www.rfc-editor.org/rfc/rfc8493.html

## 3. Corrective implementation

Added `validate_bag_declaration()` to the LOC runner as a strict RFC 8493 v1.0 declaration check:
- exactly two lines;
- exact `BagIt-Version: 1.0` syntax;
- exact `Tag-File-Character-Encoding: <encoding>` syntax;
- reject UTF-8 BOM.

The runner now records both raw bagit-python result and strict declaration result, then compares effective validity with each fixture's expected category. This preserves transparency rather than silently overriding the raw validator outcome.

Added `tests/test_bagit_conformance_runner.py` covering valid declaration, whitespace-before-colon rejection, and wrong line count. Gate A workflow now runs both worker tests and declaration-validator tests.

Commits:
- strict declaration check: `916f35071970e1e9b490ff1ba4f30989cbbdc1f5`
- regex correction: `6bd6a80e579ee51ff415add4ece252a15b958f60`
- declaration tests: `e2c99294cf0f58e5d334013527fce816f5cdeff7`
- CI includes new tests: `2286ff28154a066dcce8c76596fc60eba1cb9dc9`

## 4. Current verification status

- Worker unit tests: PASS, 10/10 in run #41.
- LOC conformance: 4/5 in run #41; whitespace fixture mismatch identified.
- Strict declaration check: committed, not yet run in CI.
- Corrected LOC suite outcome: pending.
- Windows-only fixtures: not covered on Linux runner.
- Gate A: OPEN / NOT PASSED.

## 5. Next actions

1. Confirm CI passes strict declaration tests.
2. Rerun LOC suite and confirm all Linux-applicable fixtures match expected outcomes.
3. Add a Windows runner/job for Windows-only fixtures.
4. Add malicious manifest path traversal and concurrent object-ID reservation tests.
5. Close Gate A only after all required test categories pass with retained evidence.

No OCFL/PREMIS conformance, independent replica recovery, rights clearance, production deployment or real music ingest is claimed.
