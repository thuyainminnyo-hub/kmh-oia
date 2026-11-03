# Phase 824 — EduAutomate Learning Evidence Adapter Contract

## Status
Sandbox-only contract prototype. No live EduAutomate endpoint, credentials, network call, database write, or production integration is implemented.

## Discovery
- Existing KMH OIA LearningEvidence model supports pseudonymous learner references and separate task-performance, independent-learning, and delayed-retention scores.
- Existing TrustedSourceReceiptVerifier requires a provider-specific adapter, allowlisting, integrity/authenticity verification, execution attribution, freshness, and replay checks.
- Repository issues #99 and #101 identify missing real provider API documentation and target-host evidence prerequisites.
- No verified EduAutomate API base URL, OpenAPI document, authentication scheme, webhook signature format, or source-record-to-execution mapping was found in the inspected repository.

## Proposed normalized contract (not a vendor API)
Fields: contract_version, source_record_ref, course_ref, lesson_ref, observed_at (timezone-aware ISO-8601), and evidence mapped to LearningEvidence.
Unknown fields are rejected. Names, emails, phone numbers, health data, emotion labels, demographic attributes, and free-form profiles are not accepted. Missing measurements remain null.

## Implementation
- src/eduautomate_learning_adapter.py: strict provider-neutral contract validation and mapping.
- tests/test_eduautomate_learning_adapter.py: synthetic contract tests.
- No HTTP client, authentication, persistence, provider receipt, or external call.

## Prerequisites for provider-specific implementation
1. EduAutomate backend/API owner and official API base URL.
2. Official API documentation or OpenAPI schema.
3. Endpoint and source record type for learning evidence.
4. Authentication and secret-storage mechanism; never commit credentials.
5. Provider-supported authenticity/integrity mechanism.
6. Stable source record identifier and mapping to KMH OIA execution/evidence IDs.
7. Timestamp semantics, rate limits, retries, pagination, deletion and retention requirements.
8. Sandbox environment and synthetic test account/data.

## Validation
- python -m compileall -q src tests
- python -m unittest discover -s tests -v
- Existing repository validation workflow.
- Independent privacy and API-contract review.
- When real adapter exists: invalid signature, stale timestamp, missing attribution, timeout, unknown provider and replay tests.

## Release gates
PR remains draft until independent review and actual provider contract are available. Production remains HOLD. Synthetic tests prove only local contract behavior, not connectivity, provider authenticity, or production readiness.

## Rollback
No external calls or persistent data changes. If tests fail, do not merge; abandon this branch and retain the Phase 823 base unchanged.