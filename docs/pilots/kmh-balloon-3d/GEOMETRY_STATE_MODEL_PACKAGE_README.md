# Geometry State Model v1.0 — Package Guide

The local evidence bundle contains:
- Preserved Geometry v1 body and lower-skirt GLBs.
- Two-state scene manifest with SHA-256 hashes for both GLBs.
- Manifest validator.
- State-structure schematic and validation output.

## Validate locally

From the extracted package root:

```bash
python scripts/validate_geometry_state_manifest.py registry/geometry_state_manifest_v1.json --project-root .
```

A pass confirms manifest structure, state IDs, shared asset references, separation of the Yan-Khwe reference asset, exclusion of prohibited operational fields, and SHA-256 identity of both included GLB files.

A pass does not validate physical dimensions, visual likeness, state deformation, engineering safety, or production readiness. Geometry v1 is preserved. Geometry v2 remains HOLD until state-attributed calibrated references, independent measurements, QA, and human approval exist.
