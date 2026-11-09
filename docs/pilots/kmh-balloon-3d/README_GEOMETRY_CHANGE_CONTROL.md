# KMH_BAL_001 — Geometry Change-Control Gate v1.0

## Contents
- Locked Geometry v1 baseline with source-file SHA-256 values.
- Geometry v2 change-request template.
- Evidence-completeness validator.
- Seven regression tests and test evidence.
- Example HOLD report for an empty draft.

## Validate a draft
```bash
python scripts/validate_geometry_change_request.py \
  templates/geometry_change_request.template.json \
  --asset-root /path/to/KMH_Myanmar_Balloon_3D_Intelligence_Pilot \
  --candidate-root /path/to/geometry-v2-candidates \
  --report evidence/change_request_validation.json
```

`--asset-root` checks the immutable Geometry v1 source hashes. `--candidate-root` checks the proposed Geometry v2 file hashes. Both are optional; proposed-file verification occurs only when `--candidate-root` is supplied.

An empty draft must return `BLOCKED_HOLD`. A complete record may return only `ELIGIBLE_FOR_HUMAN_RELEASE_REVIEW`; the validator never approves, edits, merges, or deploys geometry. Both technical reviewer and project owner approvals must be documented, and a separate human release action is still required.

## Regression tests
```bash
python scripts/test_geometry_change_request.py
```

The seven tests cover expected HOLD, complete evidence, unknown state, missing owner approval, candidate hash mismatch, baseline hash mismatch and the attachment-mechanics scope guard.

No physical measurements are created by this package. Geometry v1 remains the locked baseline; Geometry v2 remains HOLD.
