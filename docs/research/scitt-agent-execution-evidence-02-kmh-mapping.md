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


## 9. Revision -02 deeper review: requirements that materially affect KMH

Checked against the Datatracker -02 text on 2026-11-12. The draft is dated November 2026, last updated 2026-11-01, and expires 2027-05-05. It remains an **active individual Internet-Draft**: it is not endorsed by the IETF and has no formal standing in the IETF standards process. Its intended status field is not a standards approval.

### 9.1 The two decision doors

The draft's core evidence model is explicit: consequential agent behavior passes through either a model-inference call or a tool call. Evidence must be emitted at both decision doors, not only at the final tool-execution layer. A model-only record without tool outcome evidence, or a tool-only record that omits model decision points, is incomplete against the profile.

KMH action: inventory every model provider/harness adapter and every tool/egress adapter; identify bypass routes; fail closed where a consequential call can proceed without its evidence decision point.

### 9.2 Eleven Signed Statement types

The -02 draft defines these eleven types: Agent Registration, Model Provider, Agent Credential, Serving Party Credential, Policy Pack, Configuration Integrity, Configuration Drift, Execution Receipt, Execution Epoch, Assurance, and Revocation.

Important semantic separation:
- Agent Registration is the long-lived logical identity and capability declaration.
- Agent Credential is the operational/runtime identity, keys, harness, model binding and sub-agent declaration for a period.
- Serving Party Credential identifies a receiving service.
- Model Provider Statement identifies a dated model version and provider-published evaluation/safeguard commitments.
- Policy Pack and Configuration Integrity are separate immutable commitments.
- Configuration Drift links a previously registered configuration digest to a new registered digest.
- Assurance is a scoped assessment, not an identity credential.
- Revocation/status statements express lifecycle state; they must be evaluated under the designated authority and freshness policy.

Do not collapse these into one KMH Agent record or one mutable profile object.

### 9.3 Assurance and independent supervision

The draft describes risk-based operational assurance and supervised status. At assurance levels 3 and 4, the assessor must be a third party organizationally independent of the Responsible Entity and operator. Where a Supervisory Authority is designated for a scheme, that authority—not the assessor—controls transitions such as RESTRICTED, SUSPENDED, restore VALID, and withdrawal. Deviations requiring immediate suspension must be reported and acted on under the scheme.

KMH action: keep assurance as a separate evidence and governance domain. Do not label KMH's own internal QA as independent third-party assurance. Do not claim accreditation; the draft explicitly does not define a universal accreditation scheme or risk classification.

### 9.4 Runtime identity, sub-agents and chain continuity

The draft distinguishes logical agent identity from runtime identities. Runtime identities have validity windows and are bound through Agent Credential Statements. Sub-agents are declared under the parent's credential and act under the parent's logical identity; they do not gain an unrelated logical identity merely because they have a separate runtime process. Credential rotation and revocation must preserve verifiable historical continuity.

KMH action: connect the current ExecutionIdentity and mandate context to a versioned credential statement model, but keep the local account/instance/environment/session key distinct from a standards-profile Runtime Identity. Add validity-window checks at receipt timestamp and parent/sub-agent linkage tests.

### 9.5 Configuration integrity, drift and policy binding

Every Execution Receipt carries both policy_pack_digest and config_integrity_digest. The configuration statement commits to ordered configuration entries with mandatory Unicode normalization. The draft specifically treats prompts, instruction files, skills, hooks, tool manifests and memory as behavior-shaping inputs. Configuration drift requires the old and new configuration statements to be registered, and the harness must detect mismatch before allowing further calls.

KMH action: build a manifest from actual loaded inputs, not a manually maintained descriptive list. Normalize and hash at load time, re-check during execution, and emit a drift event before further tool/model calls. Do not include raw secrets or private prompt contents in public receipts; use content digests and controlled evidence retention.

### 9.6 Task and confirmation semantics

Tasks are delimited by task_start and task_end receipts. A confirmation request is not an authorization outcome: a tool call without its resolving confirmation outcome is incomplete. A tool_result must not precede an allow outcome. A task must not end with a pending confirmation; if the session closes with one pending, the Evidence Service records block first.

KMH action: implement a deterministic task state machine and negative tests for missing/duplicate confirmation, wrong parent sequence, wrong task, tool result before allow, and task close with pending confirmation.

### 9.7 Request binding and privacy

The draft adds call_digest and egress_host/hosts bindings for linked admission and outbound tool/egress records. Its text warns that low-entropy request digests can be guessed by an observer. It also constrains free-text target and egress_host fields and prohibits embedding query/user/argument/parameter values in them. Natural-person Principals are represented using a peppered digest, with the pepper retained by the issuer.

KMH action: do not expose raw request digests for low-entropy sensitive values without a documented privacy analysis. Keep the pepper outside the agent process. Use constrained host/path-template metadata and never put user arguments or payment amounts into public identifiers or free-text evidence fields.

### 9.8 Execution Epoch and offline Bundle

The draft's Bundle is CBOR and includes the required Transparent Statements, an ordered receipt-chain segment, optional inclusion paths for receipts in epochs, and status-list token snapshots. A Linked Bundle is an ordered sequence of Bundles for each Evidence Chain in a cross-operator Call Chain. Offline verification must check registration and credential relationships, policy/configuration references, epoch continuity, status snapshots, and linked caller/serving-party evidence.

KMH action: do not treat a JSON export or local SQLite dump as an AEE Bundle. Implement a versioned CBOR Bundle adapter only after statement schemas and registration policy are stable. Add deterministic offline verification and explicit status freshness reporting.

### 9.9 The draft's own implementation-status statement

The draft's authors report a prototype with harness-side model/tool decision points, hash-chained signed records, Tasks, refusals, separate approvals, and an offline verifier. They explicitly list as not implemented in that prototype COSE wrapping, epochs, Bundles, SCITT registration, per-call agent signatures, validity-window checks, Assurance checks, Principal peppering, and several -02 additions including registration/model-provider/serving-party statements, sub-agent records, memory digests, supervisory status, admission receipts and linked verification.

This is the authors' implementation-status disclosure, not an independent interoperability report. It is useful evidence that the profile is still maturing and that KMH should target the published -02 text carefully rather than assume a complete production reference implementation exists.

## 10. Updated KMH decision

1. Keep CCF receipt verification and AEE execution-evidence semantics as separate layers.
2. Next code increment should be a **KMH AEE Task/Decision-Point State Machine**, not a premature COSE Bundle implementation.
3. Add typed model/tool/confirmation/task events, sequence and parent linkage, policy/config digests, and fail-closed ordering.
4. Follow with configuration manifest/drift enforcement, then registration/credential/assurance lifecycle and offline Bundle.
5. Maintain a compatibility matrix against the exact -02 revision and record deviations. Do not claim AEE conformance or production readiness until real COSE/CBOR, SCITT registration, official vectors and independent interoperability checks pass.



## 11. AEE-1 local task/decision-point validator implementation

Added `src/aee_task_state.py` and `tests/test_aee_task_state.py` as a deliberately local, decoded-object state-machine slice. It is **not** an AEE wire-format encoder, CBOR/JCS canonical hash implementation, COSE signer/verifier, SCITT client, or profile-conformance claim.

The validator currently checks:
- Sequence starts at 0 and increments by exactly one; supplied predecessor hash matches the prior supplied 32-byte record hash.
- Every receipt has 32-byte policy-pack and configuration-integrity digests, runtime agent ID, principal, timestamp and task reference.
- Admission records are outside Tasks, use their own sequence as task_seq, and carry allow/block only.
- task_start opens an allowed Task; task_end closes only an open Task.
- Non-admission receipts belong to an open Task and preserve the Task's Principal.
- Parent sequence is earlier and present; tool_call references inference, tool_result references tool_call, egress references tool_call or inference.
- A tool_result cannot reference a confirm-pending or blocked tool_call; it must reference an allow outcome.
- Confirmation is restricted to tool_call; an outcome must be exactly one allow/block tool_call matching the earlier confirmation's parent, target, request digest and Task.
- A Task cannot close while a confirmation remains pending.
- Egress records require an egress_host.

Tests cover valid tool flow, confirmation/outcome/result ordering, pending confirmation at task close, mismatched confirmation request, wrong parent type, Principal substitution, admission-to-task linkage, and broken predecessor linkage.

### Deliberate limitations and follow-up

- record_hash is supplied to this validator; it does not recompute canonical CBOR/JCS receipt hashes. That must be done by a separately reviewed canonical encoder and signed-statement implementation.
- No full AEE CDDL validation, COSE per-call agent_sig verification, runtime credential validity-window checking, delegated task policy ancestry, sub-agent credential binding, config-drift verification, admission-basis/status freshness, actor-chain verification, SCITT registration, epoch root or Bundle validation is implemented here.
- The model/tool harness integration points are not wired by this module. A receipt sequence supplied by a caller is not proof that all real model/tool/network calls were captured. Completeness requires instrumentation at every model, tool, network and ingress decision point and negative tests for bypasses.
- The module should remain an internal state-machine primitive until official AEE Appendix A vectors and independent implementation comparisons are available.



## 12. Follow-up standards review — 2026-11-12

### 12.1 Decision Point coverage is explicitly three-sided

The current -02 text defines Decision Points as the combination of policy decision, enforcement and evidence recording. It identifies:
- Harness model door: every inference.
- Harness tool door: every tool invocation, its result and resulting egress.
- Serving Party ingress door: every received call.

This sharpens the KMH instrumentation requirement: model/tool interception alone is insufficient for cross-operator trust. A receiving service must independently emit admission evidence for each received call. The caller's chain explains why it made the call; the serving party's chain explains what it admitted and why. Linked verification compares both chains to detect omission.

**KMH gap:** the local validator accepts admission records and can bind a task_start to an earlier allowed admission, but it does not instrument an actual inbound serving endpoint or prove that every received call creates exactly one admission receipt.

### 12.2 Task interleaving and delegated Tasks

The -02 Evidence Chain semantics permit receipts from different Tasks to interleave. Each receipt still names an earlier allowed task_start whose Task remains open; each Task has at most one task_end; and each receipt's Principal must match its own task_start Principal.

A delegated Task has additional constraints:
- task_start identifies an earlier task_start of a still-open parent Task;
- it carries the same Principal as the parent Task;
- its policy_pack_digest equals the parent's digest or identifies a registered descendant Policy Pack whose parent chain includes the parent's pack;
- the profile notes that effective-scope no-wider-than-parent cannot yet be checked mechanically.

**KMH gap:** the current local validator can represent multiple open Tasks and enforce per-task Principal continuity, but it does not yet model delegated_from or validate Policy Pack ancestry. It also does not compare effective delegated scope. Do not imply delegated-task conformance.

**Next implementation:** add an explicit delegated-task relation and a trusted Policy Pack ancestry resolver. Reject unknown, cyclic, unregistered or non-descendant policy lineage. Keep semantic strictness and scope attenuation as separately reviewed policy assertions; a digest relationship alone does not prove that a child policy is stricter.

### 12.3 Hash-chain semantics and privacy

The draft requires record-hash over canonical CBOR (or JCS for JSON), sequence 0 with a 32-byte zero predecessor, and exact sequence increments. It warns that low-entropy request digests can be guessed and recommends limiting digest exposure through epoch-root registration and retention controls. It also notes that a response digest commits to what the Decision Point received, not necessarily what the agent was ultimately given if the harness transforms or withholds it.

**KMH gap:** the current validator checks supplied digest sizes and predecessor linkage, but does not recompute canonical record hashes or prove the receipt corresponds to the content delivered to the model/tool. Keep those as separate cryptographic and harness-integrity gates.

### 12.4 Standards maturity — checked 2026-11-12

- **AEE -02:** active individual Internet-Draft, last updated 2026-11-01, expires 2027-05-05. Datatracker explicitly states it is not IETF-endorsed and has no formal standing in the IETF standards process.
- **CCF Profile -06:** active SCITT WG Internet-Draft, last updated 2026-10-22, with WG state "Submitted to IESG for Publication" and IESG state "Waiting for AD Go-Ahead". It is not yet a published RFC. The draft specifies CCF COSE receipt inclusion and consistency proofs, and requires all proofs in the receipt to recompute the same newer root.
- **SCRAPI -11:** active SCITT WG Internet-Draft with IESG approval as Proposed Standard recorded in the June 2026 protocol-action announcement. The current draft record still shows the Internet-Draft document and an expiry of 2026-12-28; do not call it a published RFC unless the RFC Editor record confirms publication.

### 12.5 Updated engineering sequence

1. Complete the current decoded-receipt validator and retain its explicit non-cryptographic boundary.
2. Add tests for interleaved Tasks and then delegated Task semantics with trusted Policy Pack ancestry.
3. Instrument all three Decision Point domains: model, tool/egress and serving ingress.
4. Add canonical CBOR/JCS record-hash recomputation and exact -02 CDDL validation; reject duplicate CBOR map keys and non-canonical encodings as required by the selected profile.
5. Add serving-party admission receipts and linked cross-operator verification.
6. Build epoch and offline Bundle support only after statement schemas, registration policy, credential/status validation and cryptographic adapters are stable.

No AEE conformance, production readiness or complete call-capture coverage is claimed by this follow-up.


## 13. AEE validator increment — interleaving and timestamp ordering

Following the -02 Task semantics review, the local decoded-receipt validator now:
- permits multiple open Tasks whose receipts interleave in one Evidence Chain, while retaining per-receipt Task membership and per-Task Principal continuity;
- enforces non-decreasing receipt timestamps across the chain, including Admission Receipts;
- rejects boolean timestamps (Python bool is an int subclass and must not pass timestamp validation).

New tests cover two interleaved Tasks, decreasing timestamps, and boolean timestamps. This remains a local semantics check: it does not implement delegated Task delegated_from relationships or registered Policy Pack ancestry, and does not prove Decision Point capture completeness.
