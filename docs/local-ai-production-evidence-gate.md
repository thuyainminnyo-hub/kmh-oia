# Verified Output → Evidence Gate

Status: IMPLEMENTED ON PILOT BRANCH; CI FOR THIS REVISION PENDING

`create_verified_evidence` composes the existing filesystem containment/non-empty
file gate with `ProductionEvidence.from_output`. It refuses missing or
out-of-root outputs before hashing. Evidence defaults to QA `pending`.

This is an in-process helper. It does not invoke ComfyUI, persist audit events,
sign the manifest, or provide semantic/content QA. A valid digest establishes
byte identity only, not image quality or safety.

Run:
```bash
python -m unittest tests.test_production_evidence_gate -v
python -m unittest discover -s tests -v
```
