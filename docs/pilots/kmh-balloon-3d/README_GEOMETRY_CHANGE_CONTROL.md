# KMH_BAL_001 — Geometry Change-Control Gate v1.0

## Contents
- Locked Geometry v1 baseline with source-file SHA-256 values.
- Geometry v2 change-request template.
- Evidence-completeness validator.
- Nine portable positive/negative regression tests.
- Example HOLD report for an empty draft.

## Validate a draft

```bash
python scripts/validate_geometry_change_request.py \
  templates/geometry_change_request.template.json \
  --asset-root /path/to/KMH_Myanmar_Balloon_3D_Intelligence_Pilot \
  --candidate-root /path/to/geometry-v2-candidates \
  --report evidence/change_request_validation.json
```

Both `--asset-root` and `--candidate-root` are mandatory for eligibility. The validator checks the locked Geometry v1 source files and proposed candidate files against their recorded SHA-256 values. Missing roots or mismatched files cause `BLOCKED_HOLD`.

An empty draft must return `BLOCKED_HOLD`. A complete record may return only `ELIGIBLE_FOR_HUMAN_RELEASE_REVIEW`; the validator never approves, edits, merges, or deploys geometry. Technical reviewer and project-owner approvals, followed by a separate human release action, remain mandatory.

## Regression tests

```bash
python scripts/test_geometry_change_request.py
```

Nine tests cover:
1. Empty request fails closed.
2. Complete synthetic evidence reaches only human-release review eligibility.
3. Unknown target state is rejected.
4. Missing project-owner approval is rejected.
5. Candidate hash mismatch is rejected.
6. Baseline hash mismatch is rejected.
7. Attachment-mechanics inference is rejected.
8. Missing candidate root is rejected.
9. Missing baseline root is rejected.

Synthetic bytes exercise metadata/hash control only; they are not real GLBs and do not replace mesh QA.

No physical measurements are created by this package. Geometry v1 remains the locked baseline; Geometry v2 remains HOLD.
