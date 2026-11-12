# SCITT Agent Execution Evidence -02: KMH OIA Research & Implementation Mapping

**Research date:** 2026-11-12  
**Reference:** https://datatracker.ietf.org/doc/draft-thaha-scitt-agent-execution-evidence/02/  
**Status:** Active individual Internet-Draft; not endorsed by the IETF and has no formal standing in the IETF standards process. Do not treat it as an adopted SCITT WG standard or published RFC.

## 1. Executive finding

This draft is unusually relevant to KMH OIA because it addresses the evidence gap between agent identity/authorization and what an agent actually did. It describes a SCITT profile for signed records of model calls, tool calls, admission decisions, cross-operator call chains, offline verification and evidence bundles.

Recommendation: use the draft as a research input and gap-analysis target, not as a normative production dependency. Keep KMH's existing Agent Trust and Execution Evidence modules; add an explicitly versioned AEE-profile adapter only after a schema and threat-model review. Do not rename the local prototype as AEE-conformant.

## 2. Relevant profile concepts

The -02 draft describes:

- **Agent Registration Statement:** persistent logical identity and declared capability profile, registered with a Transparency Service.
- **Agent Credential Statement:** runtime identities, key, harness, model binding and sub-agent relationships for an operational period.
- **Policy Pack Statement:** versioned policy lineage and policy digest.
- **Configuration Integrity Statement:** digest commitments to system prompts, instruction files, skills, hooks, tool manifests and memory/configuration inputs, with normalization rules.
- **Execution Receipt:** per-decision-point record for model/tool/egress activity, including allow/deny/block outcomes and request digests.
- **Evidence Chain:** ordered receipts linked by predecessor digest, scoped to an Agent Credential or Serving Party Credential.
- **Admission Receipt:** evidence produced by the receiving/serving party.
- **Linked Evidence Chains:** caller and serving-party records linked across operator boundaries.
- **Execution Epoch Statements and Bundles:** support registration and offline verification of receipt segments, including required statements and status-token snapshots.

The draft's model/tool "doors" are important: an evidence design that records only final tool calls but misses model inferences, tool results, or egress decisions is incomplete relative to this profile.

## 3. KMH OIA existing implementation map

| AEE concept | Existing KMH module | Current status / gap |
|---|---|---|
| Agent identity and runtime identity | src/execution_identity.py, src/agent_trust.py | Local identity model; not a registered AEE Agent Registration Statement or verifiable workload credential |
| Mandates / delegated authority | src/mandates.py | Local signed-mandate and authority-assertion interfaces; not the AEE credential/registration wire schema, nor production issuer/key lifecycle |
| Per-call execution evidence | src/execution_evidence.py | Local canonical-JSON receipt and request digest; no AEE CBOR schema, COSE Signed Statement, model/tool decision-point coverage, or policy/config references required by the draft |
| Evidence chain | src/execution_evidence.py | In-memory hash chain; no signed epoch statement, remote registration or independently anchored chain |
| Serving-party admission | src/linked_evidence.py | Caller/admission binding and SQLite local ledger; not yet an AEE Admission Receipt schema or remote SCITT registration |
| Caller/serving-party linking | src/linked_evidence.py | Local request/caller receipt linking; no interoperable linked-bundle format or full cross-operator credential validation |
| Transparency receipt verification | src/receipt_verification.py, src/scitt_receipt_verification.py | CCF proof orchestration and adapter boundary; real strict CBOR/CDDL/COSE cryptographic adapter and official differential vectors remain outstanding |
| Durable audit | src/durable_audit.py, src/linked_evidence.py | SQLite local persistence and hash-chain checks; not external WORM/independent anchoring or a SCITT Transparency Service |
| Offline evidence bundle | Existing evidence/production modules | No AEE-compatible Bundle builder/verifier and status-token snapshot evaluation demonstrated |

## 4. Material gaps to close before claiming profile compatibility

1. **Decision-point completeness:** define and test interception/recording for every model inference, tool invocation, tool result, and egress action. Include denied and blocked outcomes.
2. **Configuration integrity:** introduce a versioned configuration manifest for system prompts, instruction files, skills, hooks, tool manifests and memory inputs. Define exact canonicalization/Unicode normalization and runtime-loaded-input boundaries. Record start/end memory-state digests only where privacy and data-minimization policy permits.
3. **Policy binding:** every relevant receipt must bind the policy-pack digest and configuration-integrity digest in force. Add policy pack ancestry and validation; do not infer policy identity from a mutable local version string.
4. **Task semantics:** model task start/end, parent/delegated tasks, pending approvals/confirmations, and the rule that a tool result cannot precede an allow outcome. A pending confirmation at task/session closure must resolve to a block outcome.
5. **Credential lifecycle:** separate persistent logical agent identity from short-lived runtime identities; bind keys, validity windows, model/harness and sub-agent credentials. Add revocation/status-list evaluation and key rotation.
6. **Cross-operator linking:** make caller reference, serving-party admission, request digest, and evidence-chain linkage interoperable and independently verifiable.
7. **Transparency and offline verification:** define a Bundle containing the required transparent statements, receipts/proofs, and status-token snapshots; verify it offline against configured trust anchors.
8. **Privacy and security:** minimize or selectively disclose prompts, tool payloads, outputs and memory. Hashes prove binding, not that captured content is truthful or that an agent behaved safely. The profile itself does not provide universal accreditation or risk classification.

## 5. Recommended KMH implementation sequence

### AEE-0 — Profile boundary and threat model
- Freeze the exact draft revision used for experiments (-02).
- Write a KMH profile compatibility matrix and explicit deviations.
- Threat-model evidence omission, replay, cross-chain splicing, config drift, policy substitution, compromised harness, dishonest evidence service, key rotation, status-list staleness and privacy leakage.
- Keep the existing local receipt format versioned and separate from AEE wire types.

### AEE-1 — Decision-point coverage
- Add typed events for model_request, model_result, tool_call, tool_result, egress, task_start, task_end, confirm, and admission.
- Enforce sequence, predecessor digest, task/parent references and allow-before-result ordering.
- Add negative tests for missing events, reordered events, duplicate sequence, wrong task and unclosed confirmation.

### AEE-2 — Configuration and policy commitments
- Add immutable Configuration Integrity Statement and Policy Pack Statement models.
- Require their digests on each execution receipt.
- Canonicalize deterministically and test Unicode normalization, duplicate manifest names, invisible code points and runtime-loaded resources.
- Avoid storing raw secrets or unnecessary prompt/output contents.

### AEE-3 — Identity and linked chains
- Map current logical/runtime identity and mandate records to registration/credential statements without conflating their semantics.
- Add serving-party credential and admission receipt schema.
- Test cross-operator caller references and request-digest consistency.

### AEE-4 — Bundle and independent verification
- Build versioned offline Bundle serialization and verifier.
- Include required statements, receipt proofs and status snapshots.
- Verify signature chains, TS inclusion/consistency, revocation/status freshness, credential validity and evidence-chain continuity offline.
- Differential-test CCF receipt verification against official CCF implementations and profile vectors.

### AEE-5 — Governance integration
- Evidence completeness and cryptographic validity are separate gates.
- Missing/invalid evidence => HOLD or DENY; do not silently promote.
- A cryptographically valid receipt proves a statement was logged and bound to a log state; it does not prove the underlying claim is true or the agent's action was safe.
- Require independent security review before production trust decisions.

## 6. Acceptance criteria

- Every required decision point is recorded exactly once or has an explicit failure/omission record.
- Each receipt binds logical agent, valid runtime credential, task, policy digest, configuration digest, request digest, decision and predecessor.
- Task and cross-agent call chains cannot be spliced or reordered without detection.
- Revoked/expired credentials and stale status snapshots are rejected according to a documented policy.
- Offline Bundle verification produces a deterministic pass/fail report and identifies missing evidence.
- KMH and an independent verifier agree on CCF receipt accept/reject outcomes for official and adversarial vectors.
- CI runs against the exact commit being reported; no prior-head result is reused as proof for later code.

## 7. Standards references and status

- AEE -02 Datatracker document: https://datatracker.ietf.org/doc/draft-thaha-scitt-agent-execution-evidence/02/ — active individual Internet-Draft, last updated 2026-11-01; no formal IETF standards standing.
- SCITT Working Group documents/status: https://datatracker.ietf.org/wg/scitt/documents/ — current WG list includes AEE -02 as an individual draft.
- CCF Profile -06: https://datatracker.ietf.org/doc/html/draft-ietf-scitt-receipts-ccf-profile-06 — active SCITT WG Internet-Draft, not a published RFC.
- Microsoft CCF receipt verification: https://ccf.dev/main/use_apps/verify_tx.html — documents offline receipt verification and service-identity/endorsement checks.
- CCF Python receipt API: https://ccf.dev/main/audit/python_library.html — documents ccf.receipt.root, verify, check_endorsements, check_cert_chain, and verify_cose.

## 8. Decision

Adopt AEE -02 as a **research-alignment target only**. Do not claim AEE conformance. The next implementation priority is AEE-1 decision-point completeness, followed by configuration/policy commitments and a versioned offline Bundle. Keep CCF cryptographic verification as a separate independently validated dependency.
