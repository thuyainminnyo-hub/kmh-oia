# KMH_BAL_001 — State-Separated Capture Field Protocol v1.0

This package defines how to collect traceable visual references for the two balloon appearance states without mixing them into one reconstruction dataset.

## Files
- `STATE_SEPARATED_CAPTURE_FIELD_PROTOCOL_V1.md` — field protocol, safety/permission boundary, view coverage, image handling, scale provenance and COLMAP acceptance gate.
- `templates/capture_set_manifest.template.json` — one state-specific capture-set manifest.
- `templates/image_register.template.csv` — per-image metadata and SHA-256 register.
- `templates/coverage_matrix.template.csv` — view coverage and missing-view declaration.
- `scripts/validate_capture_manifest.py` — metadata/state consistency validator.
- `registry/capture_protocol_package_manifest.json` — package state and authorization gates.

## Workflow
1. Create a new capture-set folder for one subject and one confirmed visual state.
2. Use `BASE-UNLOADED`, `DISPLAYED-ATTACHED`, or `UNKNOWN`; do not guess the state.
3. Preserve original image files and EXIF metadata; create edited derivatives separately.
4. Fill the JSON manifest, image register and coverage matrix.
5. Run:

```bash
python scripts/validate_capture_manifest.py path/to/manifest.json
```

To check local original files and hashes:

```bash
python scripts/validate_capture_manifest.py path/to/manifest.json --originals-dir path/to/originals --require-images
```

The validator checks metadata and state consistency only; it does not certify photo quality, measurement accuracy or reconstruction readiness.

## Reconstruction gate
COLMAP remains blocked until one state-specific capture set passes human review. COLMAP's official guidance recommends good surface texture, similar illumination, high overlap, seeing each object region in at least three images, and camera movement between viewpoints rather than rotation-only capture: https://colmap.github.io/tutorial.html

Tripo paid generation requires separate explicit approval. Geometry v2 remains HOLD. Production is not authorized.

## Scope boundary
This is non-operational heritage documentation only. Do not touch, move, load, unload, suspend or alter the balloon or any attached component to obtain images. Photograph only where access is permitted and safe. If a view cannot be safely captured, mark it not captured.

No new capture was performed by creating this protocol.
