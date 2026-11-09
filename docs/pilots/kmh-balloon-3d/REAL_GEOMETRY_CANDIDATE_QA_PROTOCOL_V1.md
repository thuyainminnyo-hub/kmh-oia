# KMH_BAL_001 — Real Geometry Candidate QA Protocol v1.0

## Scope
Structural checks for non-operational visual-heritage GLB candidates only. This pipeline does not calculate balloon operation, pyrotechnics, loading, attachment mechanics, lift, ignition, timing, or flight behavior.

## Checks performed
- File exists and is non-trivial in size.
- GLB can be loaded by the mesh parser.
- At least one triangle mesh is present.
- Vertex coordinates are finite.
- Face indices are valid.
- Each mesh is watertight and has consistent winding.
- SHA-256 and normalized-space bounds/extents are recorded.

## Checks not performed
- Physical scale or dimensional accuracy.
- Source-owner confirmation or image provenance.
- Camera calibration or photogrammetry readiness.
- Silhouette/artwork fidelity.
- BASE-UNLOADED vs DISPLAYED-ATTACHED deformation measurement.
- Engineering, structural, thermal, pyrotechnic, launch, or operational suitability.

## Interpretation
`STRUCTURAL_QA_PASS_REQUIRES_EVIDENCE_REVIEW` means only that the mesh files passed the listed structural checks. It is not a Geometry v2 promotion decision. `promotion_authorized` is always false.

## Run
```bash
python scripts/qa_geometry_candidate.py \
  --body path/to/body.glb \
  --lower-skirt path/to/lower_skirt.glb \
  --state UNKNOWN \
  --output evidence/candidate_qa.json
```

The state should remain `UNKNOWN` unless reliable source evidence confirms it. The pipeline deliberately blocks the evidence-review handoff for UNKNOWN state while still recording mesh diagnostics.
