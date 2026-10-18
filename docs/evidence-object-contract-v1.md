# KMH OIA — Evidence Object Contract v1.0

## Purpose

An evidence object is a stable, immutable record that links an observed artifact to the execution context that produced it. It is the evidence boundary between runtime observation, QA, later learning admission, and decision change.

This contract does **not** implement durable storage, verify external URLs or artifacts, establish business outcomes, admit learning, or authorize production deployment.

## Required provenance

Every object must identify:

- `evidence_id`: stable unique identifier assigned by the caller.
- `kind` and `source`: what the evidence represents and which system produced it.
- `observed_at`: RFC-3339 date-time with an explicit timezone.
- `scope`: the workflow, pilot, target, or evaluation scope.
- `source_revision`: source-code or workflow revision that produced the observation.
- At least one of `run_id`, `command_id`, `trace_id`, or `execution_id`.
- At least one of `artifact_ref` or `sha256_digest`; include both when practical.
- Optional `config_version` and `agent_version` when applicable.

The digest is a content identifier, not proof that the artifact is truthful. A reference is a locator, not proof that the referenced artifact remains available.

## Validation states

| State | Meaning | Minimum gate |
| --- | --- | --- |
| `OBSERVED` | Runtime or operator recorded an observation; not independently verified. | Required provenance and artifact reference/digest. |
| `VERIFIED` | A named verification record exists. | All OBSERVED requirements plus `validation_ref`. |
| `OUTCOME_LINKED` | A separately recorded outcome is linked to the evidence. | VERIFIED requirements plus `outcome_ref`. |

State labels are assertions requiring supporting records. The constructor validates presence and shape only; it does not perform verification or independently validate the outcome. Do not promote an object from OBSERVED based solely on a successful runtime response or structural QA PASS.

## Immutability and privacy

The Python contract uses a frozen dataclass. Corrections should create a new evidence object and preserve the prior identifier/reference for auditability rather than mutating an existing record.

Do not store secrets, access tokens, credentials, or unnecessary personal/customer data in evidence fields. Prefer controlled artifact references and content digests. Apply access controls and retention policies at the eventual persistence layer.

## Learning and decision boundary

- Evidence creation does not mean learning is admitted.
- `VERIFIED` does not mean a business outcome was achieved.
- `OUTCOME_LINKED` requires an explicit outcome reference but does not itself prove causality.
- Learning admission must be a separate gated record with evidence references and an explicit policy/approval result.
- Decision change must be a separate record containing before/after state, rationale, authorization, and regression evidence.
- Keep automatic learning disabled until those services and gates are implemented and tested.

## Implementation and verification

- Python model: `src/evidence_object.py`
- JSON Schema: `schemas/evidence-object.schema.json`
- Focused tests: `tests/test_evidence_object.py`

The schema and model are intended to stay aligned. CI must pass on the exact pull-request head before this slice is considered verified. A passing test suite proves contract behavior under tests only; it does not establish durable evidence storage or production readiness.

## Acceptance checklist

- [x] Required provenance fields are defined.
- [x] RFC-3339 timestamps with timezone are required.
- [x] Artifact reference or SHA-256 digest is required.
- [x] Validation-state prerequisites are explicit.
- [x] Python object is immutable.
- [x] Focused unit tests cover the principal invariants.
- [ ] Run repository test suite and validation on the exact PR head.
- [ ] Review schema/model parity and merge only after human review.
- [ ] Implement durable evidence storage and retrieval.
- [ ] Implement separate learning-admission and decision-change services.
- [ ] Verify a controlled Studio workflow with inspectable evidence.
