# KMH OIA — Evidence Object Contract v1.0

## Purpose

An evidence object is a stable, immutable record that links an observed artifact to the execution context that produced it. It is the evidence boundary between runtime observation, QA, later learning admission, and decision change.

The current implementation includes a local JSONL persistence prototype. It is **not production-grade durable storage** and does not verify external artifacts, establish business outcomes, admit learning, or authorize production deployment.

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

## Local JSONL store boundary

`src/evidence_store.py` provides a small append-only JSONL prototype:

- append a validated `EvidenceObject`;
- reject duplicate IDs in the current process and on reload;
- read one object by ID;
- list objects by trace ID in append order;
- reject malformed persisted records during load.

Tests use temporary directories and cover round-trip reads, recreation/reload, duplicate protection, trace filtering/order, invalid input, and fail-closed loading.

**Limitations:** locking is per store instance/process, not cross-process; flush is not equivalent to an fsync-backed crash-durability guarantee; there is no authentication/authorization, backup/restore, tamper-evident log, retention enforcement, or multi-node storage. Treat this as a local prototype, not a production evidence service.

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
- Model tests: `tests/test_evidence_object.py`
- Local JSONL prototype: `src/evidence_store.py`
- Store tests: `tests/test_evidence_store.py`

The schema and model are intended to stay aligned. CI must pass on the exact pull-request head before this slice is considered verified. Passing tests prove only the behaviors exercised by those tests; they do not establish production readiness.

## Acceptance checklist

- [x] Required provenance fields are defined.
- [x] RFC-3339 timestamps with timezone are required.
- [x] Artifact reference or SHA-256 digest is required.
- [x] Validation-state prerequisites are explicit.
- [x] Python object is immutable.
- [x] Focused model tests cover principal invariants.
- [x] Local JSONL prototype and focused store tests are present.
- [x] Repository test and validation workflows passed on commit `9ed59ae9b9808d478a8c47217c2b185f7fd3a646`.
- [x] Add Draft 2020-12 JSON Schema validation and model/schema parity test cases using the pinned `jsonschema[format]` development dependency; CI result for this commit remains pending until Actions completes.
- [ ] Human review and merge decision.
- [ ] Replace local prototype with storage meeting durability, concurrency, access-control, backup, and recovery requirements.
- [ ] Implement separate learning-admission and decision-change services.
- [ ] Verify a controlled Studio workflow with inspectable execution and QA evidence.


## Controlled execution evidence pilot

`src/pilot.py` runs the deterministic local runtime, checks trace integrity,
writes a JSON artifact containing the response and ordered trace events, hashes
that artifact, and appends an `OBSERVED` EvidenceObject to the local JSONL store.
Run it with:

```bash
python -m src.pilot "controlled pilot hello"
```

This is a controlled integration pilot only. It does not independently validate
the output quality, create a QA verdict, resolve the source revision automatically,
or prove an outcome. The pilot defaults `source_revision` to `unresolved` unless a revision is passed
explicitly via the Python argument or `--source-revision` CLI flag. The pilot
does not independently prove that supplied revision corresponds to the running
working tree; callers must verify it before using the record as release evidence. It must not
promote evidence to `VERIFIED` or `OUTCOME_LINKED` without separate review and
outcome records.
