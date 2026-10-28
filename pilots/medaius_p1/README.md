# KMH OIA × Medaius P1 — Patient History Retrieval

**Status:** implementation draft on an isolated branch; tests have not yet been executed in this environment. No Medaius API connection exists.

## Scope

- Local CLI/service only; synthetic JSON fixtures only.
- Exact `patient_id` matching; no fuzzy matching or inference.
- Read-only retrieval; source fixture must remain unchanged.
- Duplicate exact IDs fail closed.
- Audit events include request ID, UTC timestamp, action and outcome only; no patient ID or history content.
- No network calls, real patient data, credentials, clinical writes, deployment or production access.

## Run locally

From the repository root:

```bash
python -m unittest tests.test_medaius_p1 -v
python -m pilots.medaius_p1.cli \
  --fixture pilots/medaius_p1/fixtures/synthetic_patients.json \
  --patient-id SYN-PAT-0001 \
  --request-id local-demo-001 \
  --audit-file .local-evidence/audit.jsonl
```

Expected success exit code: `0`; exact ID not found: `2`; duplicate exact IDs blocked: `3`; invalid input/fixture: `1`. The CLI output for a successful lookup contains the synthetic fixture record. Do not use real patient identifiers or data.

## Acceptance criteria

1. Exact ID returns only the unique matching record.
2. Unknown or near-match ID returns `NOT_FOUND` without fuzzy matching.
3. All visits and observation fields in the selected fixture are preserved.
4. Duplicate IDs fail closed.
5. Retrieval does not mutate the loaded record or fixture file.
6. Audit event has request ID, timestamp, action and outcome, and excludes patient ID/history.
7. Malformed fixture and empty ID fail safely.
8. Output is deterministic for a given fixture and ID except the audit timestamp.
9. No outbound network, Medaius API call, production access, or clinical write is performed.

## Verification evidence to capture

- Full `python -m unittest tests.test_medaius_p1 -v` output and exit code.
- Positive, not-found and malformed-fixture CLI output/exit codes.
- Fixture SHA-256 before/after retrieval to prove no file mutation.
- Environment/runtime version and commit SHA.
- Review that no real PHI, secrets, or external calls were introduced.

## Integration gate

Public Medaius documentation mentions webhooks and data export/import, but webhook events are not proof of a patient-history read API. Before any adapter is implemented, obtain written confirmation of supported patient/encounter read endpoints, authentication and scopes, sandbox availability, rate limits, audit requirements, data-processing terms and integration permission from Medaius. Until then, API integration remains **PENDING**.
