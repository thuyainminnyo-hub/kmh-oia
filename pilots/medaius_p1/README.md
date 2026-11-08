# KMH OIA × Medaius P1 — Patient History Retrieval

**Status:** implementation draft on an isolated branch. Candidate head before this documentation-only update, `a10dbe708d37110e224d90d8550ba7625b6c2d3c`, passed the dedicated synthetic pilot tests, general KMH OIA tests and repository validation (run links are recorded in PR #140). This documentation update will produce a new head, so rerun and verify all workflows against the resulting SHA before treating that new head as validated. These checks validate repository/test behavior only; they do not establish Medaius API compatibility, clinical safety, or production readiness. No Medaius API connection exists.

## Scope

- Local CLI/service only; synthetic JSON fixtures only.
- Exact `patient_id` matching; no fuzzy matching or inference.
- Loader and public retrieval boundary require `synthetic: true` and the `SYN-PAT-` identifier prefix.
- These markers are guardrails, not proof that data is synthetic; fixture provenance must still be controlled and verified by the operator.
- Read-only retrieval; source fixture must remain unchanged.
- Duplicate exact IDs fail closed.
- Audit events include a constrained request ID (1–80 safe characters), UTC timestamp, action and outcome only; no patient ID or history content.
- If requested audit persistence fails, the CLI withholds the result, writes a non-sensitive error to stderr and returns exit code `4`.
- No network calls, real patient data, credentials, clinical writes, deployment or production access.

## Run locally

From the repository root:

```bash
python -m unittest discover -s tests -p 'test_medaius_p1.py' -v
python -m pilots.medaius_p1.cli \
  --fixture pilots/medaius_p1/fixtures/synthetic_patients.json \
  --patient-id SYN-PAT-0001 \
  --request-id local-demo-001 \
  --audit-file .local-evidence/audit.jsonl
```

Expected exit codes: success `0`; exact ID not found `2`; duplicate exact IDs blocked `3`; invalid input/fixture `1`; audit persistence failure `4`. The CLI output for a successful lookup contains the synthetic fixture record. Do not use real patient identifiers or data.

## Acceptance criteria

1. Exact ID returns only the unique matching record.
2. Unknown or near-match ID returns `NOT_FOUND` without fuzzy matching.
3. All visits and observation fields in the selected fixture are preserved.
4. Duplicate IDs fail closed.
5. Retrieval does not mutate the loaded record or fixture file.
6. Audit event has request ID, timestamp, action and outcome, and excludes patient ID/history.
7. Malformed fixture, missing/false synthetic marker, non-synthetic ID prefix and empty ID fail safely.
8. Output is deterministic for a given fixture and ID except the audit timestamp.
9. If audit persistence fails, retrieved output is withheld and the CLI returns exit code `4`.
10. No outbound network, Medaius API call, production access, or clinical write is performed.

## Verification evidence

- Candidate head before this documentation-only update: `a10dbe708d37110e224d90d8550ba7625b6c2d3c`
  - Medaius P1 local synthetic pilot tests #16: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40732089010
  - KMH OIA Tests #1129: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40732088777
  - KMH OIA Validation #1048: https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/40732088661
- These three runs completed successfully for the pre-update candidate SHA. The new documentation commit must be validated against its own SHA before the PR's latest head is considered CI-verified.
- The acceptance suite checks fixture SHA-256 before/after retrieval to detect file mutation.
- Review that no real PHI, secrets, or external calls were introduced.

## Integration gate

Public Medaius documentation mentioning webhooks or data export/import is not proof of a patient-history read API. Before any adapter is implemented, obtain written confirmation of supported patient/encounter read endpoints, authentication and scopes, sandbox availability, rate limits, audit requirements, data-processing terms and integration permission from Medaius. Until then, API integration remains **PENDING**.

## Review and release gate

PR #140 remains a draft and unmerged. Independent review is still required. Do not merge or deploy until the review is complete and the integration evidence gates are satisfied.
