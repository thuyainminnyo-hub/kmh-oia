# Local AI Production Pilot — Evidence Manifest

Status: IMPLEMENTED ON PILOT BRANCH; AUTOMATED CI REQUIRED FOR CURRENT REVISION

## Purpose
Create a small, deterministic manifest for a verified output file. The manifest includes job ID, adapter name, resolved output path, SHA-256 digest, byte size, elapsed milliseconds, optional provider execution ID, and QA decision.

## Safety and evidence boundary
- `ProductionEvidence.from_output` requires an existing, regular, non-empty file and calculates SHA-256 from its bytes.
- The default QA decision is `pending`; evidence generation never approves an asset.
- A digest proves byte identity for the recorded file, not that the image is valid, safe, or visually acceptable.
- The caller remains responsible for first enforcing the output-root containment gate and recording provider execution ID when the adapter exposes it.
- This is a serializable manifest object only. Durable storage, tamper-evident signing, external audit transport, and automatic trace integration are not implemented here.

## Verification
```bash
python -m unittest tests.test_production_evidence -v
python -m unittest discover -s tests -v
```
