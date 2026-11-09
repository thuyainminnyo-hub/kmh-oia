# KMH_BAL_001 — Geometry Change-Control Gate v1.0

## Contents
- Locked Geometry v1 baseline SHA-256 registry.
- Geometry v2 change-request JSON template.
- Change-control policy.
- Evidence-completeness validator.
- Empty-request HOLD evidence.

## Validate a draft

```bash
python scripts/validate_geometry_change_request.py \
  templates/geometry_change_request.template.json \
  --asset-root /path/to/KMH_Myanmar_Balloon_3D_Intelligence_Pilot \
  --report evidence/change_request_validation.json
```

The empty template is expected to return `BLOCKED_HOLD`. A fully evidenced request may return only `ELIGIBLE_FOR_HUMAN_RELEASE_REVIEW`; it never authorizes a merge or deployment. Both technical reviewer and project owner must approve separately.

The local package validation produced 30 blockers for the empty draft and verified both Geometry v1 source-file hashes. The baseline meshes were not modified.

Geometry v1 remains preserved. Geometry v2 remains HOLD. This gate covers non-operational visual heritage geometry only.
