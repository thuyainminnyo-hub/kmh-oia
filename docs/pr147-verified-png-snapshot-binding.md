# PR #147 follow-up — Verified PNG to immutable evidence binding

## Scope

This follow-up closes the gap between PNG parsing and evidence creation. The
PNG validator now returns the exact bytes it parsed together with their SHA-256
and byte length. The execution bridge carries that result to the evidence
pipeline. The pipeline stores those bytes directly in a content-addressed
snapshot and creates evidence only after the snapshot digest and size match
the validator's result.

The evidence path no longer reopens the mutable output path for image jobs.
The original output path remains provenance metadata only; the evidence hash,
size, snapshot reference, and verification version identify the immutable
bytes admitted by the gate.

## Failure behavior

- A missing or incomplete PNG integrity result fails the image pipeline.
- A missing snapshot store fails image evidence admission.
- A byte payload whose digest or size differs from the validator result is
  rejected before snapshot metadata or an `evidence_created` audit event is
  written.
- Snapshot reads re-check metadata, byte count, and SHA-256.
- Evidence remains `qa_pending`; this gate does not approve visual quality,
  policy compliance, or production promotion.

## Adversarial regression coverage

The pipeline test replaces the source output file after PNG verification and
before evidence admission. Evidence must still resolve to the original bytes
returned by the validator, not the replacement file. A second test substitutes
the verified-byte payload without changing the expected digest/size; the job
must fail with no evidence and no audit event.

## Limits

The snapshot store is local to one host and filesystem. It is not encrypted,
remotely replicated, signed, or protected from a privileged host administrator.
Atomic hard-link publication and descriptor-relative no-follow reads are
required; unsupported platforms fail closed during snapshot retrieval. No live
ComfyUI execution, production deployment, or merge is part of this follow-up.

## Verification

Focused tests:

```bash
python -m unittest tests.test_image_integrity tests.test_production_execution tests.test_production_pipeline tests.test_production_evidence_gate tests.test_verified_snapshot_store -v
```

Repository-wide test and validation workflows must pass on the exact follow-up
head, followed by independent review. Production remains HOLD until all gates
and owner-controlled release conditions are satisfied.
