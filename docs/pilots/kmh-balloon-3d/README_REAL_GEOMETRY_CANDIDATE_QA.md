# Real Geometry Candidate QA v1.0

Install: `pip install trimesh numpy`

Run:
```bash
python scripts/qa_geometry_candidate.py \
  --body /path/to/KMH_BAL_001_BODY_BLOCKOUT_v1.glb \
  --lower-skirt /path/to/KMH_BAL_001_LOWER_SKIRT_BLOCKOUT_v1.glb \
  --state UNKNOWN \
  --output evidence/geometry_v1_structural_qa.json
python scripts/test_qa_geometry_candidate.py
```

The tool checks GLB loading, mesh presence, finite vertices, valid face indices, watertightness, winding consistency, SHA-256, and normalized bounds. It does not establish physical accuracy, visual fidelity, source provenance, or authorize Geometry v2. UNKNOWN state intentionally yields BLOCKED_HOLD even when topology passes.
