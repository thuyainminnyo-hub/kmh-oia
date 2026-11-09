# Geometry Change-Control Regression Tests v1.0

## Purpose
Guard the fail-closed behavior of the Geometry v2 change-control validator. Tests use synthetic temporary candidate files and never edit the preserved Geometry v1 source meshes.

## Test cases
1. Empty change request remains `BLOCKED_HOLD` and both locked baseline file hashes match.
2. Complete synthetic evidence package reaches only `ELIGIBLE_FOR_HUMAN_RELEASE_REVIEW`, not auto-approved, with both candidate asset hashes verified.
3. `UNKNOWN` target state is rejected.
4. Missing project-owner approval is rejected.
5. Proposed candidate body hash mismatch is rejected.
6. Locked Geometry v1 baseline hash mismatch is rejected.
7. Attachment-mechanics inference is rejected.

## Result
All seven regression tests passed in the local Python test run. The empty request returns `BLOCKED_HOLD` with 30 blockers. The complete synthetic fixture returns `ELIGIBLE_FOR_HUMAN_RELEASE_REVIEW`, which is an evidence-completeness result only; it is not a real Geometry v2, approval, merge, or production authorization.

## Candidate file integrity
The validator supports `--candidate-root` and verifies proposed body/lower-skirt file SHA-256 values against the change request. Baseline and candidate file checks are reported separately.

## Run
```bash
python scripts/test_geometry_change_request.py
```
