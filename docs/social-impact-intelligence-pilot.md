# KMH Social Impact Intelligence (KMH-SII)

## Pilot 01: Evidence-Based Scam & Platform Transparency Auditor

**Status:** Initial implementation proposal on a dedicated pilot branch. Not production-ready.

### Purpose
Provide evidence-first triage for platform-related complaints. The pilot highlights explicit, verified observations for human review. It does not determine criminal intent, make legal findings, or label a person or company fraudulent.

### Scope and exclusions
- Local deterministic rules and synthetic test data first.
- No live gambling platform integration, authenticated scraping, or collection of behavioral biometrics.
- No automated account bans, public accusations, financial transfers, or reports to authorities.
- Do not ingest unnecessary personal data. Redact account numbers, addresses, phone numbers, and other identifiers from development examples.
- Pending or rejected evidence cannot trigger risk signals.
- A risk signal prompts verification; it is not proof of wrongdoing.

### Initial risk signals
- Additional payment requested after a withdrawal request.
- Withdrawal delay with no clear timeline.
- Account restriction without a stated explanation.
- Conflicting transaction records.

### Architecture
`PlatformCase → Evidence validation → Deterministic risk rules → Human review recommendation → Audit event`

The current audit chain is in-memory and intended only for local tests. It is not durable, tamper-proof storage, and must not be described as a production audit service. SHA-256 can help compare file integrity when computed from original bytes; it does not prove that a document's contents are true or authentic.

### Verification
Run in a repository checkout:

```bash
python -m unittest tests.test_social_impact_auditor -v
python -m unittest discover -s tests -v
```

Record the exact commit and test output. Do not report tests as passing until the commands have actually run.

### Exit criteria
1. All new unit tests pass.
2. Existing test suite passes.
3. Review confirms unverified evidence cannot trigger a risk signal.
4. Audit-chain mutation test passes.
5. Human-review and privacy policies are approved before real-user data is accepted.

### Known limitations
- No persistent case database or authenticated user interface.
- No independent verification of source documents.
- No calibrated statistical model or real-world performance metrics.
- No legal or jurisdiction-specific advice.
- Production release remains on HOLD until security, privacy, retention, ownership, and operational controls are reviewed.
