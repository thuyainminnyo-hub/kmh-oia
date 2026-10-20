# Evidence Admission Gate Contract

Status: IMPLEMENTED IN CODE; AUTOMATED TESTS WRITTEN; TEST EXECUTION NOT YET VERIFIED

## Purpose
Prevent unsupported claims of learning or external success. The gate evaluates supplied evidence metadata; it does not independently authenticate third-party systems.

## Required fields
- `execution_id`: stable execution identifier to which the evidence refers.
- `source`: named source or source-record locator.
- `raw_observation`: the directly observed value, separated from interpretation.
- `verification_status`: one of `UNKNOWN`, `OBSERVED`, `VERIFIED`, `OUTCOME_LINKED`.
- `outcome_linked`: explicit declaration that a real outcome is linked to this execution.

## Admission policy
- Missing execution ID, source, or raw observation => `NOT_ADMITTED`.
- `UNKNOWN`, `OBSERVED`, or `VERIFIED` alone => `NOT_ADMITTED` for learning admission.
- Learning admission requires `OUTCOME_LINKED`, the outcome-linked flag, all required fields, explicit source authentication, and execution-to-outcome attribution verification.
- Caller-supplied status and boolean attestations are not sufficient for admission. The gate now fails closed until a trusted source-receipt verifier/adapter is integrated.
- The current `source_authenticated=true` and `attribution_verified=true` fields are attestations only, not cryptographic or provider-side verification.
- Invalid status values fail closed as `UNKNOWN`.
- Interpretation is retained separately and does not substitute for raw observation.
- Admission evaluates the consistency of supplied metadata. It does not, by itself, establish that a source is genuine or that external attribution is correct.

## Evidence integrity
- Internal QA pass is not external business validation.
- Missing data is not a negative outcome.
- Publication, exposure, engagement, inquiry, booking, and business success are distinct events.
- Never invent a source, raw observation, or outcome to complete the loop.

## Implementation
- Module: `src/evidence_admission_gate.py`
- Tests: `tests/test_evidence_admission_gate.py`
- Test suite has not yet been observed passing; run `python -m unittest discover -s tests -v` in a suitable checkout before claiming test success.
