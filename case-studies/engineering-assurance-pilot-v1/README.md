# KMH OIA — Engineering Assurance Pilot V1

**Status:** Initial assurance package proposed on an isolated feature branch. Repository inspection is read-only so far; the checks described here are not yet executed against a local checkout.

## Objective
Add an evidence-first assurance workflow for architecture, security, data, runtime, and AI-agent engineering without modifying the OIA runtime core or running production actions.

## Scope and safety
- Target repository: `thuyainminnyo-hub/kmh-oia`
- Base snapshot: `7c2a0b3702ad253bcfef9e0b77125fc09275f2d8`
- Execution boundary: GitHub branch + CI only; no production credentials, deployment, live traffic, or external service calls.
- Audit scope is an inventory of repository surfaces. A surface marked `NOT_ASSESSED` is not a security finding and is not a pass.
- Existing Creative Studio Graphify G4 HOLD and consumed one-run extraction approval remain unchanged.

## Six-stage workflow
1. **Reconnaissance:** map runtime boundaries, critical assets, data stores, trust boundaries, and CI entry points.
2. **Coverage-led review:** assess architecture, security, data, runtime/reliability, delivery, and agent/tool surfaces independently.
3. **Finding challenge:** require source location, reproducible evidence, impact path, and counter-evidence; record disagreements.
4. **Risk decision:** classify confirmed, needs validation, accepted risk, or rejected/false positive. Human owner decides acceptance.
5. **Independent verification:** a reviewer who did not author the finding/fix verifies evidence, test results, and report consistency.
6. **QA and release decision:** schema/coverage checks, tests, human approval, and rollback readiness. This pilot never deploys.

## Current inventory
See `contracts/scope-inventory.json`. Inventory entries deliberately begin as `NOT_ASSESSED`; this prevents architecture discovery from being misrepresented as a completed security audit.

## Findings and evidence
- Findings contract: `contracts/finding.schema.json`
- Evidence ledger: `artifacts/evidence-ledger.json`
- Decisions require an evidence reference and reviewer identity.
- No secrets, tokens, private data, production logs, or unapproved external assets may be copied into artifacts.

## Local validation
From repository root:
```bash
python -m unittest discover -s case-studies/engineering-assurance-pilot-v1/tests -v
python case-studies/engineering-assurance-pilot-v1/scripts/validate_assurance_package.py
```

## Gate semantics
- **PASS:** required evidence exists and validator/test passed.
- **FAIL:** evidence demonstrates a failed requirement.
- **BLOCKED:** prerequisite or permission is missing.
- **NOT_RUN:** no execution evidence exists.
- **NOT_ASSESSED:** an inventory item has not yet been reviewed.

No overall assurance PASS is possible while any required domain remains NOT_ASSESSED, any Critical/High finding is unresolved, independent verification is missing, or human approval is absent.
