# KMH OIA Evidence-Aware Knowledge Engine — Integrated Pilot V1

## Decision

Selected approach: **C — Integrated Pilot**.

The pilot integrates a deterministic evidence-backed KnowledgeSource adapter into the existing OIA context assembly boundary. It does not replace the runtime, security policy, state store, or trace contracts.

## Runtime integration

`Goal → Input Gateway → OIA Core → Context Assembly → EvidenceKnowledgeSource → Workflow → Agent → Existing Governed Tool → Evaluation → Response → Trace`

The current runtime already accepts an injectable `KnowledgeSource` in `OIARuntime`. The pilot uses that existing seam; it does not modify the core runtime composition or widen the tool allowlist.

## Evidence lifecycle

1. Candidate: immutable source identity, locator, owner, capture timestamp, content and SHA-256.
2. Validate: require source identity, source URI, locator, owner, non-empty content and matching SHA-256.
3. Activate: only a validated candidate becomes retrievable.
4. Retrieve: only active records are returned through the KnowledgeSource port, with citation-ready provenance.
5. Verify: a claim must reference active, valid evidence; insufficient or inactive evidence fails closed.
6. Audit: caller retains normal OIA trace events. Persistent audit storage is not part of this in-memory pilot.

## Implemented contracts

- `EvidenceRecord`: source identity and integrity metadata.
- `EvidenceRegistry`: candidate/active separation and validation.
- `ClaimVerifier`: fail-closed evidence checks and citation output.
- `EvidenceKnowledgeSource`: adapter implementing the existing `KnowledgeSource.retrieve(goal)` interface.
- `tests/test_evidence.py`: focused standard-library unit tests.

## Explicit limitations

- In-memory registry only; restart durability and distributed consistency are not implemented.
- No live external ingestion, crawler, embedding model, vector database, or graph database.
- A matching token is retrieval relevance, not semantic proof that a claim is entailed.
- SHA-256 proves byte consistency against the recorded digest, not source authenticity or truth.
- Source owner identity is a supplied field; the pilot does not authenticate the owner.
- Activation is a local pilot operation, not an independent production approval workflow.
- Existing OIA tool authorization remains unchanged.

## Verification plan

Run:

```bash
python -m unittest tests.test_evidence -v
python -m unittest discover -s tests -v
```

CI must pass on the exact feature-branch head SHA. Then inspect the workflow run and review the diff before opening/merging a PR.

## Release gates

- G0 Source and provenance contract: implemented; source authenticity remains unverified.
- G1 Candidate/active separation: covered by unit tests.
- G2 Hash integrity and fail-closed claim verification: covered by unit tests.
- G3 Existing OIA KnowledgeSource seam: adapter implements the existing protocol.
- G4 Full repository CI on branch head: pending GitHub Actions result.
- G5 Independent review and human approval: pending.
- Production deployment / promotion: NOT AUTHORIZED.
