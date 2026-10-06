# Operating Intelligence — Operating Loop Contract

Status: READY FOR IMPLEMENTATION

## Canonical loop

Context → Operating Intelligence → Registry → Master Character Lock → Scene Prompt Assembly → Execution Bridge → Real Execution → Event/Audit → QA → Evidence → Learning → Decision Change → Next Execution

## Contract IDs

Every stage must preserve traceability through stable IDs:

- context_id
- decision_id
- registry_record_id
- lock_id
- prompt_id
- execution_id
- event_id
- qa_id
- evidence_id
- learning_id
- change_id
- experiment_id
- version
- timestamp

## Evidence boundary

Model QA is not external validation. Generated content is not publication. Publication is not exposure. Exposure is not inquiry. Inquiry is not booking. Missing evidence remains UNKNOWN.

## Admission rule

A learning update may be admitted only when evidence is sourced, mapped to an execution, and has a clear raw observation. Verified outcome evidence is required before claiming externally validated improvement.

## Current implementation gate

- Architecture: READY
- Execution flow: READY
- Evidence contract: READY
- Decision-change contract: READY
- Experiment contract: READY
- External measurement channel: NOT YET VERIFIED
- EXEC-SUN-TRAVEL-005: HOLD

## Definition of done

A vertical slice is complete when one context can be traced from input through decision, registry retrieval, identity lock, prompt assembly, execution, audit, QA, evidence capture, learning admission, and a traceable next decision.
