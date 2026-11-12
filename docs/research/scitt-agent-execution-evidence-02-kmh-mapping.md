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


## 14. SCRAPI interoperability follow-up — status and KMH adapter review (2026-11-12)

### 14.1 Standards status rechecked

- AEE -02 remains an active **individual** Internet-Draft, published November 2026, expires 2027-05-05, and explicitly has no formal standing in the IETF standards process.
- CCF Profile -06 remains an active SCITT WG Internet-Draft. Datatracker history records IANA expert review as OK and approval of the COSE VDS algorithm registration on 2026-11-10. The WG page still reports "Waiting for AD Go-Ahead" and "Submitted to IESG for Publication"; it is not yet a published RFC.
- SCRAPI -11 is further along: the WG page reports IESG RFC Editor Queue, and the RFC Editor state is Awaiting First Editor / In Progress. It is still not a published RFC as of this check.

### 14.2 SCRAPI requirements that affect the KMH client boundary

SCRAPI -11 defines the interoperable HTTP API surface for:
- GET /.well-known/scitt-keys returning a COSE Key Set as application/cbor;
- POST /entries for Signed Statement registration, with immediate 201 receipt or asynchronous 202 registration and a Location resource;
- GET receipt resolution, with 200 receipt, 204 still pending, and 404 not found.

Operational requirements worth preserving in KMH:
- clients must handle unknown HTTP status codes by generic class semantics and inspect Concise Problem Details when present, rather than assuming a closed status-code set;
- respect Retry-After as a minimum delay when supplied;
- otherwise use exponential backoff with jitter, cap retries and avoid synchronized polling;
- do not poll aggressively; rate limiting and DoS controls are required;
- retain old Transparency Service public verification keys for as long as receipts may need verification, or provide an alternative archival mechanism;
- cache headers are hints and do not limit how long a relying party must retain keys needed for its receipts.

### 14.3 Existing KMH code review

The feature branch contains two overlapping transport-injected SCRAPI adapters:
- src/scitt_client.py
- src/scitt_registration.py

Both implement key discovery, registration and receipt resolution, but their response models and validation differ. scitt_registration.py preserves Retry-After on pending responses; scitt_client.py currently drops it. Neither performs automatic retries, which is a safe default until a caller-owned bounded polling policy is defined. Neither performs CBOR decoding, COSE signature verification, or network I/O without an injected transport.

**Recommendation:** consolidate around one canonical adapter and one shared response/error model before wiring a production transport. Preserve the no-implicit-retry default, but expose Retry-After, classify 429/5xx and malformed Problem Details, and provide a caller-driven bounded retry policy with jitter. Add tests for 201/202/200/204/404/429/5xx, missing or malformed Location, cross-origin Location, wrong media types, malformed error bodies, Retry-After propagation, key rotation and retired-key retention. Do not let an adapter's successful HTTP response imply a cryptographically valid receipt.

### 14.4 Current CI verification checkpoint

On 2026-11-12, branch head 193cf8f7dfc8a0033a09689803ccea0f746d01a6 was checked:
- KMH OIA Tests: completed successfully (run 2134).
- KMH OIA Validation: completed successfully (run 2049).

This CI result covers the current branch head at that time. The open PR remains a draft; successful CI does not constitute production deployment, external interoperability, security review, or AEE conformance.

### 14.5 Next engineering increment

1. Consolidate the two SCRAPI client adapters and define one typed registration/receipt state model.
2. Propagate Retry-After and structured error details without automatic unbounded polling.
3. Implement a bounded caller-controlled retry helper with exponential backoff + jitter and testable clock/random injection.
4. Add verification-key archival/rotation policy and explicit trust-anchor configuration.
5. Keep receipt cryptographic verification independent from HTTP protocol success.


## 15. Standards-status correction — CCF Profile -06 (2026-11-12)

A subsequent check of the live Datatracker record supersedes the earlier statement in Section 14.1 that IANA expert review was OK and the VDS algorithm registration had been approved. The current -06 page shows:
- IANA review state: Version Changed — Review Needed.
- IANA expert review state: Issues identified.
- The expert comment requests proof-type registrations, including an inclusion proof and potentially a consistency proof, and a table entry explaining which proofs VDS algorithm 2 produces.
- WG state remains Submitted to IESG for Publication; IESG state remains Waiting for AD Go-Ahead.

Therefore KMH must not treat the CCF Profile -06 IANA registrations as settled. Keep the COSE VDS algorithm and proof-type handling behind a versioned adapter, pin the exact draft and IANA registry snapshot used in tests, and re-check the current IANA review before interoperability claims. This is a standards-status correction, not a change to the local verifier's claimed capabilities.

The branch's latest documentation-only commit is 5c73e83fade203daaac39a12c6d54200a7937df0. The preceding code-bearing commit 193cf8f7dfc8a0033a09689803ccea0f746d01a6 had both KMH OIA Tests and KMH OIA Validation pass. No CI run was returned for the documentation-only head; do not report that head as newly CI-tested.


## 16. Appendix A conformance-vector opportunity and IANA status reconciliation (2026-11-12)

### 16.1 AEE Appendix A contains concrete receipt examples

Revision -02 includes worked Execution Receipt examples with explicit record hashes, including:
- Task start (seq 0, zero predecessor);
- Model inference (seq 1);
- Tool call with a confirmation decision (seq 2);
- subsequent task/tool outcome examples and an admission receipt;
- example policy/configuration digests and receipt-chain values.

These examples are suitable as a source for a version-pinned fixture set. They should be transcribed exactly from Appendix A, preserving CBOR integer labels, byte strings, timestamps, canonical encoding, and the draft's stated record hashes. A test should independently recompute each canonical receipt hash and compare it to the published vector, then feed the decoded records through the KMH semantic validator. Do not fabricate expected values from the prose excerpt or substitute the current test factory's synthetic hashes.

**Current KMH gap:** the local tests create synthetic record_hash values and the validator trusts supplied hashes. It does not yet parse the Appendix A CBOR examples or recompute canonical-CBOR/JCS record hashes. Therefore current tests are state-machine tests, not AEE Appendix A conformance tests.

### 16.2 Important AEE semantics to preserve in fixture mapping

- Record types are task_start, task_end, inference, tool_call, tool_result, egress and admission.
- Decision-point values are model, tool, network and ingress.
- Decisions are allow, block, confirm and record.
- Every receipt carries policy_pack_digest and config_integrity_digest.
- A confirm is a tool_call decision; its outcome is a later tool_call carrying confirm_seq and matching parent_seq, target, request_digest and Task.
- A tool_result cannot precede the allow outcome.
- A Task cannot close with a pending confirmation; the Evidence Service records block before closure/session-loss completion.
- The receipt record-hash includes agent_sig when present.
- Natural-person Principals are represented by a 32-octet peppered digest; the pepper remains with the Issuer.

### 16.3 CCF Profile IANA status — reconcile live history

The CCF Profile -06 landing page and its history view were inconsistent in the retrieved Datatracker snapshots. The revision history explicitly records on 2026-11-10 that the IANA Experts State changed to Expert Reviews OK and that the COSE Verifiable Data Structure Algorithms registration was approved. The landing-page IANA summary snapshot still displayed older "Issues identified" text. For this research record, prefer the dated revision-history event for the 2026-11-10 action, but re-check the live registry and landing-page state before making an external standards claim. The WG/IESG publication status remains Submitted to IESG / Waiting for AD Go-Ahead; the draft is not yet a published RFC.

### 16.4 Latest branch verification checkpoint

The exact documentation head a438e6942ed1d2cccb39c068041c3c0e712c84d2 was checked on 2026-11-12:
- KMH OIA Tests: completed successfully (run 2136).
- KMH OIA Validation: completed successfully (run 2051).

This confirms repository CI for that exact head. It does not establish AEE vector conformance, canonical encoding correctness, COSE verification, external SCRAPI interoperability, or production readiness.

## 17. WIMSE companion research and first Appendix A semantic fixture (2026-11-12)

### 17.1 Companion draft discovered: Evidence Binding for AI Agent Credentials

The same authors' repository contains a WIMSE companion Internet-Draft, revision -03: *Evidence Binding for AI Agent Credentials*. It is an Informational WIMSE working-group document, not an adopted RFC. It deliberately narrows scope to:
- an aee_evidence claim binding a workload credential to the logical agent, expected Evidence Service and governing policy, with optional Assurance Statement;
- an in-toto predicate carrying Execution Receipts alongside an agent audit record;
- per-call admission-time assurance checking by a Serving Party;
- an AEE-Caller-Ref HTTP field linking the call to caller-side evidence;
- Principal and Actor Chain propagation across hops.

This is a useful companion to AEE: AEE describes the evidence records and transparency profile; WIMSE Evidence Binding describes how workload identity credentials tell a relying party where the evidence is expected and how a serving service links an inbound call to the caller's evidence.

**KMH implication:** do not put evidence discovery only in a local agent registry. Add a separate, versioned workload-credential evidence-binding adapter that validates the authenticated workload identity, expected Evidence Service, policy reference and optional assurance reference before admission. Keep this as an adapter boundary until WIMSE AIMS and Evidence Binding stabilize.

### 17.2 Adjacent drafts worth tracking

The companion repository also references:
- WIMSE AI Identity Management System (AIMS), for identity lifecycle and minimum agent audit requirements;
- an audit record format for AI Agent Authorization Decisions, for richer decision context;
- Authorization Evidence Chains, for composing heterogeneous authorization evidence;
- OAuth identity/authorization chaining and transaction tokens, for Actor Chain and cross-hop transaction binding.

These are separate work items and must not be represented as adopted standards merely because a companion draft references them.

### 17.3 Appendix A execution-receipt semantic fixture added

Added a test named test_accepts_aee_02_appendix_a_execution_receipt_semantics to tests/test_aee_task_state.py. It transcribes the published Appendix A execution-receipt example's:
- four supplied record hashes and predecessor sequence;
- task_start and model inference records;
- tool_call confirmation and matching allow outcome;
- policy/configuration digests, principal digest representation, request digest, target, timestamps and parent/confirmation references.

This fixture exercises the existing decoded-object state machine against published values instead of only synthetic sequential hashes.

**Strict limitation:** this is a semantic fixture using the Appendix A values, not full Appendix A cryptographic conformance. The test currently supplies the published record hashes to the validator; it does not parse the COSE files, encode canonical CBOR, independently recompute the four receipt hashes, or verify the per-call Ed25519 COSE signature. The public author repository's vectors/make_vectors.py and vectors/vectors.txt are valuable reproducible reference material; pin the exact source commit and generated vector checksums before importing binary fixtures into KMH.

### 17.4 Current verification boundary

The fixture was committed at code commit 3e6544ffdc8efbcb1c98a4914be94ad13efb1ee2. No workflow run had been returned for this exact commit at the time of this update. Do not report the new test as passing until CI completes on this head. The preceding documentation head 6c03f67dfbe70b8985c01c9f3857af31109ae9f6 had no workflow run returned either; the last verified head remains the earlier code-bearing commit a438e6942ed1d2cccb39c068041c3c0e712c84d2, whose two repository workflows passed.

### 17.5 Recommended next gate

1. Pin the AEE author repository commit and checksum vectors/vectors.txt and the relevant COSE files.
2. Add a canonical CBOR implementation with strict duplicate-map-key and canonical-encoding checks.
3. Recompute Appendix A record hashes and compare byte-for-byte with the published values.
4. Parse and verify COSE_Sign1 protected headers, Sig_structure and Ed25519 signatures using the test keys only.
5. Add tamper tests: changed payload byte, changed protected header, wrong key, wrong agent identity, wrong predecessor hash, altered request digest, and invalid confirmation linkage.
6. Add a distinct WIMSE evidence-binding admission adapter and tests for missing/incorrect Evidence Service, stale assurance, policy mismatch and caller-reference linkage.

## 18. WIMSE AIMS -01 and Evidence Binding -03 precise integration contract (2026-11-12)

### 18.1 WIMSE AIMS -01 is now the current WG draft

The IETF Datatracker lists draft-ietf-wimse-aims-01, published 2026-11-02, as an active WIMSE Working Group Internet-Draft with intended status Informational and expiry 2027-05-06. It is a conceptual Agent Identity Management System, not a product or a finalized protocol. Its functions include identifiers, credentials, credential provisioning, authentication, authorization, observability/remediation, policy, and compliance.

KMH should map these as interfaces/capabilities rather than duplicate a parallel identity protocol. The existing KMH Registry and Trust Governance remain the local control plane; standards adapters should consume established workload identity, OAuth and SPIFFE mechanisms where appropriate.

### 18.2 Evidence Binding -03 claim fields: distinguish required from optional

The current -03 draft's aee_evidence object has these fields:
- REQUIRED: evidence_service (CBOR key 1), policy_pack_digest (2), logical_agent_id (5).
- OPTIONAL: transparency_service (3), agent_credential_digest (4), assurance_statement_digest (6), assurance_level (7), assurance_status (8), registration_digest (9), and status_checked_at (10).

The optional assurance_level and assurance_status are a paired signed cache; they are not authoritative on their own. The freshness rule concerns the age of status_checked_at, not the token's remaining lifetime. High-risk operations SHOULD check the status list directly. If agent_credential_digest is present, the represented public key in the Agent Credential Statement MUST equal the token's cnf key; without this binding the claim supplies identity/policy correlation, not credential-key-bound evidence. The claim names the expected Evidence Service; it does not identify a particular Bundle or provide a retrieval protocol.

### 18.3 Serving Party admission contract

Before acting on each call, the Serving Party must:
1. Validate the token and request proof-of-possession under the applicable profiles.
2. Resolve the applicable Assurance and Registration Statements and enforce policy freshness.
3. Verify accepted issuer/authority, validity, assurance level and permitted status.
4. Evaluate the Principal and current actor against operation policy. Prior Actor Chain entries are attribution/history only and MUST NOT be used as admission authority inputs.

For AEE-Caller-Ref, the Serving Party recomputes call_digest over the request it actually received; it never trusts the caller-provided digest. It refuses a mismatch, refuses a missing digest when linking is required, and MUST refuse a caller reference it has already admitted. The per-call reference must not be put in a reusable token that can be presented on multiple calls. The Serving Party records its own computed call_digest in its admission receipt.

The -03 changes section notes a nuanced replay limitation: behind a shared gateway host, a wrong-backend admission can still pass when only that admission is in the Linked Bundle. KMH should therefore bind backend/service identity and request-target routing context into its local admission policy and tests; caller-reference uniqueness alone is not a complete cross-backend replay defense.

### 18.4 Actor Chain is attribution, not delegated authority

The draft explicitly states that nested act claims carry asserted actor history. Prior actors are informational only for admission. They do not prove that each hop possessed authority or narrowed it. If KMH needs authority attenuation across multiple agents, it must verify per-hop signed delegation evidence or linked receipts; do not infer authority from the Actor Chain.

### 18.5 Standards maturity boundary

AIMS -01 is a WIMSE Working Group Internet-Draft. Evidence Binding -03 is an individual Internet-Draft associated with WIMSE discussion, not a WG-endorsed standard and not an RFC. Keep both behind versioned adapters and pin draft revisions in conformance tests. Avoid describing either as an adopted standard or assuming IANA registrations are already assigned.

## 19. WIMSE Identifier -04, cross-domain mandates and local per-call proof (2026-11-12)

### 19.1 WIMSE Identifier -04: identity syntax is an authorization security boundary

The active WIMSE WG document draft-ietf-wimse-identifier-04 (2026-10-23) defines Workload Identifiers as absolute URIs with a non-empty authority/trust-domain and path. It prohibits query, fragment, userinfo and port components; rejects literal or percent-decoded dot segments; requires URI syntax normalization followed by complete normalized-URI byte comparison; and requires trust-domain validation against configured trust anchors/authorized issuers. A plain identifier string outside a cryptographically validated credential MUST NOT be treated as authenticated.

KMH implementation requirements:
- Keep an internal immutable logical-agent UUID, but introduce a versioned external WIMSE identifier field.
- Parse and validate the complete URI before normalization; never authorize by path-only comparison.
- Maintain an explicit trust-domain / issuer allowlist and bind it to credential verification.
- Do not equate an external service DNS name or network route with the workload identity.
- Preserve retired identifiers and their audit references; never silently recycle an identity.

The WIMSE Identifier draft is an active Internet-Draft, not an RFC. Pin -04 in adapter tests.

### 19.2 Cross-domain agent mandates: separate authority-to-delegate from the mandate itself

The November 2026 individual Internet-Draft *Verifiable Mandates for Agents Acting Across Administrative Domains* (draft-hulea-wimse-agent-mandate-01) addresses a gap that ordinary delegation tokens do not solve: proving that the delegator was itself entitled to grant the permissions. It separates:
1. an Authority Assertion from an authority source, describing what the delegator may delegate for the principal;
2. a root Mandate Assertion issued on the delegator's instruction and bound to the agent instance key;
3. optional narrower mandates delegated to downstream agents;
4. a relying-party validation procedure under an explicit Validation Profile; and
5. the relying party's separate authorization decision and obligations.

KMH should model a mandate as a signed assertion and never treat possession of a mandate as automatic permission. Verify the chain of authority-to-delegate, agent-key binding, scope limits, expiry and relying-party profile; then independently decide whether the requested resource/action is allowed. Token exchange must preserve the enforceable mandate semantics. This is an individual draft, not an adopted WIMSE standard.

### 19.3 Verifier-side evaluation semantics: standardize the decision, not just the chain

The WIMSE WG documents index lists *Verifier-Side Evaluation Semantics for Delegated Authority Chains* as draft-jackson-wimse-evaluation-05 (2026-10-28). Its core design principles are directly relevant:
- process every authorization_details entry or refuse; never silently ignore an unsupported permission type;
- evaluate each delegation path independently and fail closed per path;
- use an explicit evaluation instant, not the latest evidence timestamp, for expiry;
- bind approval consumption to the exact frozen call, including principal and authority context;
- separate issuer keys that raise authority from evaluator keys that lower authority;
- do not let agents write to the grant store or hold authority-raising keys.

KMH should treat these as candidate requirements for a local verifier contract, but pin and review the exact -05 text and referenced GAL/PTC drafts before claiming conformance. The draft is work in progress and is not an RFC.

### 19.4 Local MCP tool invocation is a separate enforcement boundary

The individual Internet-Draft *Per-Call Proof for Local Tool Invocation by AI Agents* (draft-lee-wimse-local-tool-call-proof-01, 2026-10-12) targets a gap not solved by HTTP workload authentication: local MCP stdio calls to filesystem, shell, database and SaaS tools may never cross an HTTP enforcement point.

Its proposed design places a Call Authority outside the agent process. The authority issues a short-lived, single-use proof bound to the exact tool name, arguments and server via a canonical action digest. The local Tool Server recomputes the digest, asks the Call Authority to verify the proof, and rejects missing/invalid proof or unavailable authority. Verification occurs immediately before execution starts, including when a queued/deferred invocation eventually starts.

KMH architecture implication:
- Add a Local Tool Enforcement Adapter at the tool-server boundary; do not rely only on OIARuntime preflight authorization.
- Keep Call Authority signing keys inaccessible to the agent process and tool server; use an isolated process and platform-protected key where feasible.
- Bind proof to exact tool, canonical arguments, server identity, authenticated process identity, request ID and policy version.
- Enforce single-use atomically at execution start; queued work must be revalidated against current policy.
- Fail closed when Call Authority is unavailable for protected tools.
- Record proof issuance, verification, consumption and final effect as distinct events in AEE evidence.

This draft is an individual Internet-Draft and has open issues around proof profiles, canonical action digest alignment, MCP method coverage and multi-effect tools. Treat it as a design input, not a stable interoperable standard.

### 19.5 Updated KMH trust decision pipeline

The resulting candidate pipeline is:
1. Authenticate the complete WIMSE workload identifier through a valid credential and trusted issuer.
2. Validate the Authority Assertion and Mandate Assertion chain under a pinned validation profile.
3. Evaluate every requested authorization detail and each delegation path at the current evaluation instant.
4. Freeze the exact action and authority context shown for any required human approval.
5. Obtain a single-use local Call Proof from an external Call Authority for protected local tool calls.
6. Revalidate proof and current policy immediately before tool execution; atomically consume the proof.
7. Record authorization, invocation, actual result/effect and linked caller/serving evidence in AEE.
8. Independently verify evidence and feed discrepancies into governance/learning; evidence never retroactively grants authority.

### 19.6 Implementation scope decision

Do not implement every draft at once. First add a KMH-local FrozenAction canonical representation and deterministic digest tests; then an atomic single-use CallProofStore and local tool-server verification adapter. In parallel, add strict WIMSE URI parsing/trust-domain tests. Keep cross-domain mandate verification as a separate follow-on because its authority-source trust model and Validation Profile need an explicit deployment decision.

## 20. Context-taint isolation research and Local Call Proof hardening (2026-11-12)

### 20.1 New proposal: Cryptographic Separation of Untrusted Context and Control-Plane Tool Calls

The WIMSE documents index lists draft-durga-wimse-ctx-isolation-00 (2026-10-29), an individual Internet-Draft proposing a Context Taint Attestation (CTA) for MCP/A2A tool invocations. It proposes a taint lattice, a context Merkle root, a signed attestation bound to each invocation, and independent step-up approval for state-mutating or privileged actions when untrusted data has entered the active context.

This is directly relevant to KMH's prompt-injection/confused-deputy threat model, but the draft is an individual proposal and is not IETF-endorsed. Treat it as a threat-model and prototype input, not an established protocol or a proof that a model's hidden internal context has been completely measured.

Important design caveat for KMH: a signed CTA proves that a trusted runtime attested to the fields it supplied; it does not by itself prove that the Merkle root covers every item actually influencing model output. KMH must define a complete, auditable context-ingestion boundary, canonical chunk representation, provenance labels, ordering, tool-output capture and reset semantics. If that coverage cannot be established, label the result as runtime-reported context provenance, not complete context attestation.

Suggested KMH policy:
- Taint is monotonic within a context/session once untrusted external content is ingested; reset requires an explicit isolated context boundary, not merely a prompt instruction.
- Separate read-only, reversible writes, irreversible/state-mutating actions and privileged actuation into effect classes.
- Untrusted or mixed context may request a sensitive action, but cannot authorize it. Require a separate policy decision or human approval bound to the exact frozen action.
- Bind CTA to the exact Action Digest and AEE receipt sequence; do not accept an unattached generic approval receipt.
- Emit an auditable rejection when the context provenance is missing, incomplete, stale or unverifiable.

### 20.2 Local Call Proof draft: verified implementation details and threat boundary

The current draft-lee-wimse-local-tool-call-proof-01 specifies Action Digest as BASE64URL(SHA-256(JCS({method, name, arguments}))), where absent arguments become an empty object and the transmitted JSON values are used without semantic normalization. The Call Authority runs outside the Agent process, identifies the caller from platform peer credentials or workload identity (never from an identity field asserted in the request body), evaluates signed/versioned policy, and issues a short-lived proof. The Tool Server computes the digest from the invocation as received and asks the Call Authority to verify it immediately before execution; a successful verification consumes the proof. Missing proof, mismatch, expiry, replay or unreachable Call Authority must not result in execution. The draft says a proof SHOULD have a validity window of 30 seconds or less.

The draft explicitly excludes a malicious/compromised Tool Server, compromise of Call Authority or policy signing key, and prevention of prompt injection itself. It also requires Agent, Tool Server and Call Authority to be in separate isolation boundaries to protect reusable secrets; otherwise the protection against credential theft is weakened.

KMH implementation refinements:
- Use RFC 8785 JCS exactly as specified for the JSON Action Digest profile; do not silently substitute CBOR or custom JSON normalization.
- Include method, exact tool name and exact arguments; bind the server identity in the proof/verification context as required by the profile, not only in a display label.
- Derive caller identity from OS peer credentials or an independently validated workload identity, never from caller-supplied JSON.
- Use an atomic consume operation (transaction/compare-and-swap) so concurrent duplicate verifications cannot both succeed.
- Verify at execution start, not enqueue time; reverify after retries or deferred scheduling.
- Pin a signed policy version and fail closed if policy is absent, invalid or rolled back.
- Separate Agent, Tool Server and Call Authority OS users/containers/process boundaries; keep Call Authority keys non-exportable where platform support permits.
- Record per-check states (passed, failed, not established), not only a single rejection reason.

### 20.3 WIMSE ecosystem update

The live WIMSE documents index currently lists AIMS -01, Identifier -04, Mutual TLS -03, Workload Credentials -03, Workload Proof Token -02 and multiple agent-specific individual drafts. It reports Workload Identity Practices -08 in IETF Last Call ending 2026-11-13, and HTTP Signatures -08 submitted to IESG for publication as Proposed Standard. These maturity states differ: the latter are further along than individual proposals but should still not be called published RFCs unless the RFC Editor confirms publication.

### 20.4 Next implementation gate

Prioritize a small local prototype, not a broad standards implementation:
1. Define FrozenAction schema and RFC 8785 JCS digest fixture tests.
2. Build a Call Authority process with OS-derived caller identity and signed, monotonic policy version.
3. Implement atomic single-use proof consumption and tests for race/replay/expiry/mismatch.
4. Put the Tool Server in a separate OS/container boundary and verify immediately before execution.
5. Add an effect-class + context-taint policy hook; require out-of-band approval for sensitive actions when provenance is untrusted or incomplete.
6. Emit AEE records for issuance, verification, consumption, execution result and rejection.

No code implementation or CI pass is claimed by this research update.

## 21. Context Taint Attestation (CTA) -00 research and KMH integration decision (2026-11-12)

### 21.1 Draft status and scope

The WIMSE/OAuth-related individual Internet-Draft draft-durga-wimse-ctx-isolation-00, published 2026-10-29, proposes a cryptographic Context Taint Attestation for MCP/A2A tool invocations. It is explicitly an individual Internet-Draft with no formal IETF standing. It proposes an Agent-Ctx-Isolation HTTP header or MCP _meta.ctxIsolation object, serialized as RFC 8785 JCS or RFC 8949 Deterministic CBOR and signed with Ed25519/COSE_Sign1. It requests new media type, header and taint-level registrations; these are requests in a draft, not assigned registry entries.

The example envelope includes invocation_id, parent_trace_ref, system_prompt_digest, data_plane_merkle_root, taint_lattice_level, tool_effect_class, step_up_receipt_hash, iat, exp and signature metadata. Its core policy is monotonic taint within a context session and fail-closed rejection of state-mutating/privileged actions from mixed or untrusted context unless an independent, valid step-up approval is attached.

### 21.2 KMH threat model and coverage limitation

CTA is relevant to indirect prompt injection and confused-deputy risk, but a valid signature proves only that the signer attested to the supplied fields. It does not prove that every item that influenced model output was captured. A data-plane Merkle root is meaningful only if KMH can establish a complete context-ingestion boundary, canonical chunk representation, ordering, source provenance, tool-output capture, truncation behavior and reset semantics.

KMH must distinguish:
- complete context capture independently demonstrated by runtime architecture and tests; versus
- runtime-reported provenance with known blind spots.

Do not claim full context attestation if hidden/system context, model-internal state, cached retrieval or tool output can influence the action without being captured. Taint should remain monotonic for a context/session after untrusted ingestion. A reset must create a new isolated context with explicit provenance, not simply append a prompt instruction saying to ignore prior content.

### 21.3 Effect-based policy

Classify actions separately: read-only, reversible write, irreversible/state-mutating, and privileged actuation. For sensitive effects, mixed/untrusted context cannot authorize the action. Require a separate policy or human step-up decision bound to the exact FrozenAction digest, principal, target tool/server, effect class, policy version and invocation ID. An approval for one action must not be reusable for another action or request.

### 21.4 Proposed KMH integration contract

Add a versioned ContextProvenance record to the local runtime, with source ID, content digest, canonical chunk digest, ingestion time, trust label and parent trace. The runtime emits a CTA only from this controlled record stream. The Local Tool Enforcement Adapter independently verifies:
1. CTA signature, key status, algorithm and validity window;
2. invocation ID and parent trace linkage;
3. recomputed FrozenAction digest and tool/server binding;
4. taint level and action effect class;
5. step-up receipt signature, freshness, single-use status and exact action binding;
6. current policy version and revocation state.

The tool server, not the LLM or caller, enforces the result immediately before execution. Failed or unavailable verification means no protected side effect. Emit AEE evidence for context ingestion, CTA creation, step-up decision, tool-proof verification, execution and final effect.

### 21.5 Interoperability and standards boundary

The CTA proposal references RFC 8785 JCS, RFC 8949 Deterministic CBOR and RFC 8032 Ed25519, but its wire profile and new headers are still draft proposals. KMH should not invent or register a competing public format. Prototype behind a private versioned adapter, keep exact profile version in test vectors, and re-evaluate if the draft changes. Do not advertise CTA interoperability or IETF conformance.

### 21.6 Implementation priority

1. Define a controlled ContextProvenance event schema and test source coverage.
2. Add monotonic taint-state transitions and explicit isolated-context reset semantics.
3. Extend FrozenAction to bind invocation ID, exact tool/server, effect class and policy version.
4. Bind independent step-up approval to the exact FrozenAction digest and atomically consume it.
5. Add CTA signing/verification as a private adapter only after key isolation and canonicalization tests.
6. Add adversarial tests for omitted tool output, reordered chunks, replayed approval, stale CTA, wrong tool/server, context reset abuse and missing provenance.

No CTA code implementation, conformance result or production security claim is made by this research update.

## 22. WIMSE delegation convergence review — current -03/-02 revisions (2026-11-12)

### 22.1 Workload Identity Practices -08 is in IETF Last Call

The WIMSE documents index currently lists draft-ietf-wimse-workload-identity-practices-08 as an active IESG Internet-Draft in IETF Last Call ending 2026-11-13, with intended publication as Informational. This is materially more mature than the individual agent-specific proposals, but it remains a draft and is not yet an RFC. Recheck the Last Call outcome and any revised version before treating it as stable deployment guidance.

### 22.2 Agent Delegation Chain -03: exact offline attenuation contract

The latest listed revision is draft-asor-wimse-agent-delegation-chain-03 (2026-10-27), not the earlier -00/-01 text. It proposes an offline-verifiable OAuth JWT chain with:
- one invariant accountable Principal in `sub` across all hops;
- each acting agent identified in `client_id`;
- holder binding through `cnf` and DPoP;
- `del_depth`, root `del_max_depth`, and monotonic expiry;
- `par_hash` committing to the exact parent JWS Signing Input to prevent chain splicing;
- exactly one `authorization_details` object of type `agent_delegation`; unsupported or additional detail types are rejected rather than ignored;
- deterministic authority subsumption for scopes and typed constraints, with child authority no wider than parent;
- bounded chain depth and explicit validation at the enforcement point.

The verifier checks signatures/accepted algorithms, parent linkage, chain shape and Principal invariance, authority attenuation, time bounds and status according to the pinned profile. The draft is an individual Internet-Draft and not IETF-endorsed or an RFC.

**Critical cumulative-budget caveat:** a `max_subtree` ceiling carried in a chain is only a signed limit. Offline verification alone does not reserve or debit a shared aggregate budget. Safe aggregate spend requires coordinated allocation (e.g. a single-writer allocator splitting disjoint child budgets) and durable local debit at enforcement points. Do not claim a global budget guarantee from token attenuation alone.

### 22.3 Credential Delegation Protocol -02: complementary online control plane

The individual draft-sweeney-wimse-credential-delegation-02 (2026-10-30) profiles existing OAuth 2.0 Token Exchange, DPoP, Rich Authorization Requests and OpenID Connect CIBA for AI agents operating across providers. It proposes ephemeral agent keys, capability-shaped delegated tokens, token wrapping so the agent does not receive underlying OAuth credentials, consent-gated asynchronous delegation, cascading revocation and tamper-evident audit chains. It explicitly defines composition of existing mechanisms rather than a new OAuth grant or token format.

This is complementary to Agent Delegation Chain -03, not a substitute:
- use an online Delegation Server / credential broker when consent, current status and cascading revocation are required;
- use offline chain verification at an enforcement point when deterministic attenuation must be checked without contacting the authorization server;
- a deployment may combine both, but must define how the online-issued child authority maps to the offline chain and how revocation/status freshness is handled.

The draft is an individual Internet-Draft, not an adopted WIMSE WG standard or RFC. Its protocol and security review are not complete merely because it composes existing RFCs.

### 22.4 KMH architecture decision: dual-path delegation, one authorization contract

KMH should avoid choosing a single draft as the universal delegation design. Introduce a common internal `DelegationDecision` contract with explicit fields: principal, acting workload identity, target resource, action/scopes, constraints, parent reference, expiry, proof-of-possession key, status freshness, policy version and verification profile.

Provide two adapters:
1. `OnlineDelegationAdapter`: consent, token wrapping, exchange and cascading revocation; status must be checked under an explicit freshness policy.
2. `OfflineAttenuationVerifier`: verify each signed hop, exact parent commitment, invariant principal, acting-agent identity, scope/constraint subsumption, bounded depth, expiry and holder proof.

Both adapters must produce the same normalized decision object and feed the same enforcement policy. Unknown authorization detail types, missing required claims, stale/unavailable status where status is required, unsupported constraints or incomplete chain must fail closed. The resource server makes the final action decision; possession of a valid chain or token is not by itself permission to perform every operation.

### 22.5 Tests required before integration

- parent JWS byte mutation and child `par_hash` mismatch;
- Principal changes at any hop;
- missing/incorrect `client_id`, `cnf`, `aud`, `del_depth` or root `del_max_depth`;
- child scope widening, constraint weakening, expiry extension and excessive depth;
- unknown/additional `authorization_details` entries;
- expired, revoked, unavailable or stale status;
- DPoP key mismatch and replay;
- token exchange preserving the enforceable scope/constraints;
- parent token remains broader after child attenuation (ensure no false assumption that attenuation revokes parent);
- concurrent sibling allocations attempting to overspend a cumulative budget.

No delegation-chain verifier or credential-broker implementation is added by this research update. No CI or interoperability result is claimed.

## 23. Revision-pinned corrections: Agent Delegation Chain -03 and Credential Delegation -02 (2026-11-12)

A direct read of the official -03 and -02 drafts refines Section 22.2/22.3 as follows. Pin these exact revisions in KMH tests; do not reuse -01 vector expectations as -03 conformance.

### 23.1 Agent Delegation Chain -03 exact profile

- `sub` is the invariant accountable Principal at every hop; `client_id` identifies the acting agent at each hop. Every token requires `client_id`, `cnf` and a non-null `aud` under this revision; legacy -01 chains without these are malformed under -03.
- `par_hash` is BASE64URL(SHA-256(parent JWS Signing Input)), where the signing input is the exact serialized protected-header and payload bytes joined by `.`. It is not a hash of a parsed/re-serialized JSON object.
- `del_depth` is required on each token; `del_max_depth` is required at the root and cannot be increased by a child. Child depth must follow the chain position and remain within the root maximum.
- Scope grammar has three byte-classified forms: literal, wildcard and opaque. Literal covers only identical literal; wildcard covers segment-bounded literal/wildcard descendants; opaque covers only byte-identical opaque scope and is never covered by wildcard. Classification is case-sensitive and ordered; invalid wildcard forms are rejected before subsumption.
- Each child must carry exactly one supported `agent_delegation` authorization detail in the profile's required shape; unsupported/additional detail types are rejected. Constraint subsumption is typed: do not compare or infer across different constraint types. `rank` ordering must remain identical; duplicate constraints with same key and type are malformed.
- Verification checks each chain independently; authorities from separate chains MUST NOT be combined. The chain binds a token instance, not a stable parent identity: reissued parent token bytes do not satisfy an existing child's `par_hash`.
- Holder binding is DPoP via `cnf` in every token. The verifier checks signature algorithm against its own configured allowlist and key configuration, not merely the token's `alg` header. Status unknown is a denial when status is present/required by profile.
- A child attenuation does not revoke its parent. A holder of the parent retains broader authority until expiry/revocation. Use short-lived tokens and status-list policy where immediate parent/subtree invalidation is needed.

### 23.2 Test-vector provenance

The -03 Appendix B publishes a new, separately named vector set. The twenty vector files from -01 are explicitly unchanged and are not -03 conformant because they lack `cnf`, `client_id` and a valid `aud`. KMH must pin and import the -03 vector set separately, verify source checksums, and assert the named expected outcomes (including principal_altered, par_hash_mismatch, not_narrower, signature_invalid and malformed). Do not silently relabel -01 vectors as -03.

### 23.3 Credential Delegation Protocol -02: server-side counterpart

The official -02 draft (published 2026-10-30, expires 2027-05-03) explicitly positions itself as the online/server-side counterpart to the offline-verifiable Agent Delegation Chain. Its Delegation Server stays in the path at each hop, can perform synchronous revocation and maintain a single-writer aggregate budget. For cases where a resource server must verify without the Delegation Server, the draft uses the Agent Delegation Chain format unchanged rather than redefining it.

The -02 draft also clarifies that `client_id` names the acting agent and must agree with `act.sub`; constraints use the shared typed vocabulary and fail-closed parsing; numeric ceilings are distinct from capability constraints and aggregate lifetime/spend totals are debited by the Delegation Server; each hop re-verifies authority and freshness. The online and offline paths are complementary but require a clearly defined issuance/verification profile and consistent status semantics.

### 23.4 Cumulative budget and revocation decision

Offline attenuation proves a signed ceiling is not widened along the chain; it does not, by itself, provide a globally serialized spend counter. If KMH needs a hard aggregate spend or call-count cap across sibling agents, route allocations through a single-writer budget authority (or a rigorously coordinated equivalent) and durably debit at enforcement. Similarly, local offline verification cannot promise instantaneous global revocation without a freshness/online status dependency. State the availability-versus-revocation trade-off explicitly in deployment policy.

### 23.5 Implementation gate

1. Vendor the exact -03 Appendix B vectors and checksums; keep -01 vectors in a separate compatibility suite only.
2. Implement strict JWS/JCS parsing, duplicate-member rejection, accepted-algorithm allowlist, `par_hash` exact-byte verification, DPoP `cnf` validation and audience check.
3. Implement typed scope/constraint subsumption, principal invariance, client identity, bounded depth and monotonic expiry.
4. Test separate chains independently; never aggregate authorities across paths.
5. Add online Delegation Server integration only after defining consent, status freshness, cascading revocation and single-writer budget ownership.
6. Report each check independently and fail closed on unknown status, unsupported constraint or malformed chain.

No KMH delegation-chain verifier or online credential broker is implemented by this research update.

## 24. WIMSE Workload Credentials -03 and Workload Proof Token -02: credential/proof separation (2026-11-12)

### 24.1 Workload credentials define two distinct credential forms

The active WIMSE WG draft draft-ietf-wimse-workload-creds-03 (published 2026-10-30; intended Standards Track; expires 2027-05-03) defines:
- Workload Identity Token (WIT): JWT credential for application-layer workload identity, binding a public key to a workload identity.
- Workload Identity Certificate (WIC): X.509 credential primarily intended for transport-layer authentication using mTLS.

The credential format is separate from proof of possession and authorization. A WIT is not a bearer token: the workload must prove possession of the corresponding private key using a separately specified binding such as WPT or HTTP Message Signatures. WIC is used by the mTLS profile. The credential draft explicitly warns that verifiers must not infer hardware-backed or non-exportable key protection merely from WIT/WIC presence; stronger key-protection claims require deployment-specific evidence/profile requirements.

### 24.2 Workload Proof Token -02 binds a proof to context, but is not full request integrity

The active WIMSE WG draft draft-ietf-wimse-wpt-02 (published 2026-08-27; intended Standards Track; expires 2027-02-28) defines a signed JWT proof of possession for the private key bound to a WIT. It includes request/context binding claims such as audience (`aud`), WIT hash (`wth`), unique proof ID (`jti`) and optional hashes for accompanying transaction or other identity/authorization tokens (`tth`, `oth`).

Verifier checks include valid signature under the WIT-bound key, expected audience, unexpired `exp`, matching `wth`, and replay handling for `jti`; unknown token types listed in `oth` cause rejection. Raw WPT values must not be logged by default. TLS with server authentication is required unless another secure channel is provided.

**Critical boundary:** the draft warns that WPT does not protect major portions of the HTTP request and response and does not protect against an actively malicious middlebox. KMH must not treat WPT as a body-integrity signature, full HTTP message signature, or a substitute for request-body/action digest binding. For sensitive calls, combine WPT authentication with a separate integrity profile (e.g. HTTP Message Signatures or the KMH FrozenAction digest) that covers the method, target and exact body/action semantics, plus server-side replay protection.

### 24.3 KMH credential verification pipeline

1. Validate the WIT JWT or WIC certificate chain, issuer/trust domain, workload identifier and validity under the selected WIMSE profile.
2. For WIT application-layer use, verify a fresh WPT or other accepted proof of possession against the credential-bound public key; never accept WIT as a standalone bearer token.
3. Validate WPT `aud`, `exp`, `wth`, `jti` replay status and any `tth`/`oth` token bindings; reject unrecognized bound token types.
4. For mTLS, validate WIC and bind the authenticated TLS peer to the expected workload identity.
5. Independently evaluate authorization, delegated authority, request/action integrity, context taint and effect class.
6. Record identity authentication, proof validation, authorization decision, action execution and result as distinct evidence events.

### 24.4 Key management and privacy requirements

- Keep private keys outside LLM context, prompts, tool arguments and ordinary logs.
- Bind each key to the correct workload identifier; rotate/reissue under explicit lifecycle policy.
- Treat compromise/disclosure of a private key as invalidating the credential's security assumptions.
- Do not claim TPM/HSM/non-exportable protection unless measured or independently evidenced by the deployment.
- Do not persist raw WPTs in ordinary logs; log identifiers and verification outcomes instead.
- Assess whether workload identifiers, target URIs or claims reveal personal information; minimize and protect logs.

### 24.5 KMH implementation gate

Add separate adapters/interfaces for `WitCredentialVerifier`, `WicMtlsVerifier`, `WptProofVerifier` and `HttpRequestIntegrityVerifier`. Add negative tests for WIT presented without proof, wrong WIT hash, wrong audience, expired proof, duplicate `jti`, wrong bound token hash, unknown `oth` token type, wrong TLS peer identity, compromised/revoked key, and request body changed after WPT verification. Pin draft revisions and keep these adapters versioned because the documents remain Internet-Drafts, not published RFCs.

No WIT/WIC/WPT code implementation, conformance result or production security claim is made by this research update.

## 25. WIMSE Workload Identity Practices -08: platform credential threat controls (2026-11-12)

The WIMSE WG Workload Identity Practices -08 is in IETF Last Call ending 2026-11-13, intended Informational RFC. It remains an Internet-Draft, not a published RFC. The draft covers Kubernetes service-account tokens, SPIFFE SVIDs, cloud instance metadata and CI/CD workload identity patterns.

KMH deployment controls derived from the draft:
- Issue separate credentials with distinct audiences for each target/resource and trust boundary; never reuse a Kubernetes API token for external federation or a different resource.
- Prefer short credential lifetimes and bind invalidation to workload instance lifecycle; where immediate invalidation is unavailable, define status-query or short-lifetime compensating controls.
- Prefer proof-of-possession over bearer credentials where supported.
- Restrict credential-file access with OS identity and filesystem controls; prefer memory-backed mounts where suitable, and account for backups/snapshots.
- Avoid environment variables for long-lived or sensitive credentials because they may leak through diagnostics, monitoring, process inspection or logs.
- Treat local metadata/workload APIs as sensitive credential boundaries; prevent untrusted input from influencing their URL, path or request parameters, and defend against SSRF and unintended command execution.
- Identify workloads using process-scoped/environment context where possible; IP-only or host-global identity is a weaker boundary.
- Protect shared local credential APIs with per-caller quotas/rate limits to prevent one workload denying credentials to others.
- Validate token type and audience according to policy; do not accept a credential merely because its signature is valid.

### KMH deployment profile

For the first production pilot, define per-service audience identifiers, credential TTL limits, instance termination invalidation behavior, credential storage location, OS-level access policy, metadata API egress restrictions, SSRF tests and proof-of-possession requirements. Document exceptions where platform capabilities prevent a control and add compensating measures. Treat the WIMSE practices document as deployment guidance, not a protocol specification or proof that the platform enforces these controls.

### Standards status correction

As of the 2026-11-12 check, Workload Identity Practices -08 is in IETF Last Call ending 2026-11-13, with IANA Review Needed and external review requests outstanding. Do not state that Last Call has completed or that publication is approved.

### Research integrity note: SADP claim from prior exploratory note

The previously mentioned “SADP Delegation Draft -01” and its claimed privacy-preserving scoped-context-disclosure protocol could not be independently verified in the official IETF Datatracker results checked for this update. Treat that earlier mention as unverified and do not base KMH architecture or implementation decisions on it unless an authoritative draft URL and content are produced. The verified WIMSE credential and proof documents above are the supported basis for this update.

## 26. Verified SADP -01 discovery, WIMSE HTTP Signatures -08 and AIMS lifecycle (2026-11-12)

### 26.1 Correction: SADP is verified; prior Section 24 research-integrity note is superseded

The official IETF Datatracker entry confirms draft-atakora-wimse-sadp-delegation-01, titled *Capability-Bound Delegation Chains with Scoped Context Disclosure for AI Agents*, published 2026-09-21, intended status Experimental, expires 2027-03-24. It is an individual Internet-Draft and explicitly has no formal standing in the IETF standards process. The earlier Section 24 statement that SADP could not be independently verified is superseded by this direct authoritative lookup.

The draft's problem framing is useful: delegation systems commonly constrain what an agent may do but do not necessarily constrain what task/context information the delegatee can see. SADP proposes to bind these two boundaries together:
- signed capability grants and nested delegation chains;
- strict attenuation (issuer continuity, action equality, resource subtree narrowing, non-increasing expiry, depth decrement and caveat accumulation);
- parent_grant_hash over canonical JSON of the complete parent grant including signature;
- encrypted task capsules and encrypted context objects;
- release of context content keys only to a principal whose valid capability chain authorizes the resource or an ancestor;
- scoped context disclosure, so a delegatee can receive a subset of task context without receiving the parent object key;
- hash-linked audit records and receiver-side verification before payload plaintext is released.

The draft itself notes that in its v0.2 capsule profile grants/audit metadata are authenticated outer fields and may be visible to brokers that store complete capsules. A future private-delegation-evidence profile is only anticipated, not specified as current behavior.

### 26.2 SADP limitations that KMH must preserve

This is a prototype proposal, not an established interoperable standard. The current draft states that it has no capability revocation; expiry is the lifetime bound, recommended to be short (minutes to hours). It also acknowledges that caveats such as delete_after_result and no_external_network are behavioral obligations: cryptography makes them attributable but cannot force a malicious holder to comply after plaintext is released. Key resolution and trusted-issuer configuration remain critical trust dependencies. A compromised holder key can exercise and further delegate its grant until expiry, subject to depth/caveat constraints.

KMH must not describe SADP as providing instantaneous revocation, full metadata privacy, or guaranteed deletion. Use short expiries, auditable issuer-key resolution, endpoint-side enforcement, and explicit status/revocation controls if adopted.

### 26.3 Relationship to WIMSE Agent Delegation Chain -03

SADP explicitly says it is intended to be reconcilable with draft-asor-wimse-agent-delegation-chain. The WIMSE chain focuses on authority attenuation; SADP adds encrypted task carriage, context-key release and scoped information access. They are not interchangeable formats. A future KMH adapter must define an explicit mapping between the authority constraints, principal/holder identities, chain parent commitments, expiry, caveats and resource identifiers; never treat a WIMSE `par_hash` as interchangeable with SADP `parent_grant_hash` because the covered byte structures differ.

### 26.4 WIMSE HTTP Signatures -08 is further along the publication path

The WIMSE WG documents index lists draft-ietf-wimse-http-signature-08, dated 2026-10-20, as submitted to IESG for publication as a Proposed Standard (publication requested 2026-10-20). It is not yet a published RFC. It is a stronger candidate for production request-integrity profiles than an individual draft proposal, subject to final IESG/RFC Editor outcome and exact implementation profile.

KMH should review its HTTP Message Signatures coverage and compare it with FrozenAction binding. Use the signature to authenticate covered HTTP components and use a separate deterministic action digest where local MCP invocation or application-level tool semantics need binding. Do not assume an HTTP signature covers an omitted body or every semantic effect unless the selected profile explicitly covers those components.

### 26.5 AIMS -01 lifecycle and session-boundary implication

The WIMSE WG AIMS -01 is a conceptual best-practices document using existing workload identity and OAuth standards rather than defining a new protocol. Its newer explanatory material highlights posture changes after credential issuance, deprovisioning, and sessions that may outlive the credentials that opened them. KMH must therefore treat credential expiry/revocation as a runtime session event: re-check at renewal/expiry boundaries and terminate or narrow long-lived sessions on deprovisioning, revocation or risk signals. Provision-time posture is not a perpetual authorization grant.

### 26.6 KMH implementation decision

1. Keep WIMSE Agent Delegation Chain -03 as the candidate authority attenuation adapter.
2. Keep SADP -01 as a separate experimental encrypted-context/scoped-disclosure adapter; do not merge its format into WIMSE tokens.
3. Prototype resource-key release only at a trusted endpoint that can validate the full chain and resource hierarchy before releasing a content key.
4. Add explicit caveat enforcement hooks and state which caveats are enforceable versus merely attributable.
5. Review HTTP Signatures -08 for HTTP request integrity; retain FrozenAction digest for local MCP and semantic action binding.
6. Add session revalidation/deprovisioning tests for credential expiry, revocation, posture change and long-lived sessions.

No SADP, WIMSE delegation, HTTP Signatures or AIMS runtime implementation is added by this research update. No conformance or production security claim is made.

## 27. WIMSE Dialog Binding -00 and authenticated multi-hop provenance (2026-11-12)

### 27.1 Verified individual proposal: Binding Agent Dialogs to WIMSE and OAuth Credentials -00

The official Datatracker entry confirms draft-reddy-wimse-oauth-dialog-binding-00, published 2026-10-30, expires 2027-05-03. It is an individual Internet-Draft with no formal IETF standing. It addresses a concrete gap: current WIMSE HTTP Signatures/WPT do not automatically cover an agent protocol's dialog context, and OAuth transaction tokens do not necessarily record which dialog they authorize.

The proposal binds three independently meaningful values:
- sender identity: WIMSE proof using the sender's WIT-bound key;
- authorization: optional OAuth transaction token recording the dialog identifier;
- dialog provenance: Dialog-Context covered by WIMSE HTTP Signature or WPT.

The protocol uses `Dialog-Context` as a placeholder HTTP field pending definition by the agent communication protocol. It includes a dialog identifier (`dlg`) and initiator workload identifier. The receiver checks that the initiator identifier matches the `sub` in the WIT used to verify the first proof. If transaction tokens are used, the transaction token's dialog context must match the Dialog-Context. A transaction token issued for one dialog must not be accepted in another.

### 27.2 Multi-hop proof chain and aggregate signatures

A single-hop WIMSE proof authenticates only the immediate sender. To establish who initiated the dialog and whether any intermediate hop changed its context, the receiver needs the proofs from the initiator and every forwarding participant. The Dialog Binding draft references draft-reddy-wimse-aggregate-signatures-01, which proposes per-hop received/forwarded digests and an aggregate signature to preserve authenticated provenance with near-constant signature size as the chain grows.

This is not equivalent to a plain trace ID, parent pointer, or unsigned AEE event list. Each hop's cryptographic proof must bind the same dialog context and relevant message components. If earlier proofs are omitted, the receiver can authenticate the last hop but cannot prove the initiator's context remained unchanged.

### 27.3 Important limitations and privacy boundary

- Dialog Binding -00 is an individual proposal and the `Dialog-Context` field name/format is explicitly a placeholder.
- WPT in this proposal authenticates requests only; it does not authenticate responses. If response integrity matters, use the applicable HTTP Signature response profile.
- The draft does not add a new replay-protection mechanism; deployments rely on the selected WIMSE proof's replay controls.
- Transaction tokens are optional. If absent, the proof still binds sender and dialog context, but there is no transaction-token dialog authorization check.
- At a trust-domain boundary, a participant creates a linked dialog; the original dialog identifier and transaction token do not cross the boundary. Authorization moves through identity chaining.
- Earlier-hop proofs disclose the workload identities of all participants to the final receiver. This is a provenance benefit and a privacy cost; KMH must define retention and audience policies.

### 27.4 KMH integration contract

Add a `DialogContext` object containing version, dialog_id, initiator_workload_id, trust_domain_id and parent_dialog_ref (the latter only as local metadata unless a future profile standardizes it). For each hop:
1. Authenticate the sender using WIT/WPT or WIMSE HTTP Signature.
2. Cover the exact serialized Dialog-Context and required request components with the selected proof.
3. Verify the transaction token's dialog binding where used.
4. Append the hop proof and received/forwarded message digests to a bounded provenance chain.
5. At the receiver, verify every required hop and ensure initiator identity and dialog context are invariant.
6. Apply trust-domain transition rules by creating a linked dialog and obtaining fresh authorization; do not forward original-domain dialog tokens across the boundary.
7. Emit AEE events referencing the verified dialog/proof chain, without treating a trace ID alone as cryptographic evidence.

### 27.5 Distinguish dialog provenance from task/context confidentiality

Dialog Binding authenticates which workload sent a message and which dialog it belongs to; it does not encrypt or minimize the semantic context visible to participants. SADP is a separate experimental proposal for scoped context disclosure. KMH must keep message provenance, authorization, and data minimization as distinct controls.

### 27.6 Revision/status reconciliation

The live WIMSE Datatracker documents index checked 2026-11-12 lists AIMS -01, Workload Credentials -03, WPT -02, Identifier -04, Mutual TLS -03 and Architecture -08 as active WG drafts. HTTP Signatures -08 is shown as submitted to IESG for Proposed Standard publication, while Workload Identity Practices -08 is in IETF Last Call ending 2026-11-13. These are not yet published RFCs based on the retrieved index. Pin revisions and re-check status before external standards claims.

### 27.7 Implementation priority

1. Define a KMH-local versioned DialogContext schema and deterministic serialization.
2. Bind DialogContext + transaction token + request body digest in HTTP signatures for HTTP agent hops.
3. For WPT-only request profiles, explicitly document lack of authenticated response proof.
4. Add multi-hop proof retention and bounded chain verification; evaluate aggregate-signature interoperability separately.
5. Add cross-dialog token replay tests, altered-context tests, omitted-hop tests, wrong-initiator tests and trust-domain boundary tests.
6. Define privacy controls for forwarding hop identities and dialog linkage metadata.

No dialog-binding or aggregate-signature implementation, conformance result, or production security claim is made by this research update.

### 27.8 Correction to the prior exploratory SADP note

SADP -01 is verified by the official Datatracker record as draft-atakora-wimse-sadp-delegation-01. The Section 26 correction is authoritative: it remains an individual Experimental Internet-Draft, not a standard. Do not confuse its scoped encrypted context disclosure with Dialog Binding's cryptographic message/dialog provenance.

## 28. WIMSE Authenticated Provenance -01: per-hop body lineage and aggregate signature boundary (2026-11-12)

### 28.1 Verified mechanism

The current individual Internet-Draft draft-reddy-wimse-aggregate-signatures-01 (2026-09-28) defines two complementary mechanisms for authenticated provenance across workload hops:

1. Each hop signs a received-body digest (`wimse-req-digest`) and the forwarded body digest (`Content-Digest`, already covered by the WIMSE HTTP Signature profile). The initiator uses the reserved input value `origin`. A verifier checks that each hop's output digest equals the next hop's input digest. Mismatch means unauthorized in-transit change; a hop that signs a different output digest records an attributable transformation.
2. An aggregate signature combines the individual hop contributions. It prevents removal of an unchanged/pass-through hop, which per-hop body-digest continuity alone cannot detect, while keeping signature size approximately constant with chain length. The draft is agnostic to the aggregate signature scheme.

The draft also covers responses with a corresponding `wimse-resp-digest` parameter. The source describes body lineage, not whole-message continuity: Content-Digest covers the body, while method, target URI, query and headers are separately covered by each hop's HTTP signature components. The verifier must not claim that the body-lineage mechanism alone protects the complete HTTP request/response semantics.

### 28.2 Threat coverage and limits

- Per-hop input/output digests detect removal or alteration of a hop that changed the body.
- The aggregate contribution additionally detects removal of a hop that signed but passed the body through unchanged.
- A hop may legitimately transform a body if its signed input and output digests record that transformation; policy must separately decide whether the transformation is authorized.
- The mechanism does not decide whether a workload is authorized to originate a request; authorization is outside this draft's scope.
- It does not replace Dialog Binding, OAuth transaction-token checks, WIT/WPT validation, or AEE semantic receipts.
- The proposal is an individual Internet-Draft, not an IETF-endorsed standard. The aggregate algorithm/profile and interoperability need separate evaluation; do not assume production-ready PQC aggregation.

### 28.3 Relationship to Dialog Binding and AEE

Dialog Binding -00 binds the dialog context and initiator to each hop's WIMSE proof and optionally binds the same dialog identifier into the OAuth transaction token. Authenticated Provenance -01 adds received/forwarded body continuity and detects pass-through hop removal. AEE -02 records the execution-level events and admission evidence, including linked evidence across operators. These answer different questions:
- Dialog Binding: which dialog and initiator does this message belong to?
- WIMSE Chain Provenance: which workloads handled the body, and where did it change?
- AEE: what execution decisions, calls, results and admissions were recorded?
- OAuth/Delegation: what action was authorized?

KMH should preserve references between these records rather than flattening them into one opaque signature or one trace ID.

### 28.4 KMH verification contract

For an HTTP agent hop chain:
1. Verify each hop's WIT and WIMSE HTTP Signature against the accepted issuer/key policy.
2. Verify required covered components for method, target, dialog context, transaction token, content digest and relevant identity proof.
3. Recompute the received and forwarded body digests; check output-to-next-input continuity and the initiator `origin` marker.
4. Verify the aggregate signature over the complete ordered hop contribution set when the selected profile requires pass-through-hop non-removability.
5. Verify Dialog-Context initiator against the first hop's authenticated WIT and check transaction-token dialog binding.
6. Apply authorization and transformation policy separately; cryptographic validity does not grant permission to transform or access the resource.
7. Emit AEE records referencing verified hop identities, digest transitions, dialog ID, authorization decision and final result.

### 28.5 Negative tests

- Remove a body-transforming interior hop; digest continuity must fail.
- Remove an unchanged/pass-through hop; aggregate verification must fail.
- Change a body between hops without a signed transformation; reject.
- Alter method, target, query, dialog context or transaction token outside covered components; reject according to signature profile.
- Substitute an aggregate from a different chain or reorder hop contributions; reject.
- Use an untrusted WIT, wrong key, invalid signature or unsupported aggregate profile; reject.
- Present a cryptographically valid transformation that violates policy; authorization gate must still reject.
- Tamper with a signed response or move it to a different request/dialog; response signature and dialog binding must fail.

### 28.6 Implementation priority

1. First implement ordinary per-hop WIMSE HTTP Signature verification and explicit covered-component profiles.
2. Add received/forwarded body digest lineage and mutation attribution.
3. Integrate Dialog Binding and transaction-token dialog checks.
4. Add aggregate-signature support behind a versioned experimental adapter only after algorithm choice, canonical contribution encoding, key lifecycle and test vectors are pinned.
5. Link the verified provenance result to AEE receipts and cross-operator Linked Bundles.

No WIMSE aggregate-signature implementation, conformance result or production security claim is made by this research update.

## 29. Revision-pinned WIMSE Chain Provenance -01 and AEE -02 verification notes (2026-11-12)

### 29.1 Authenticated Provenance -01: exact wire-level model

The Datatracker confirms draft-reddy-wimse-aggregate-signatures-01, published 2026-09-28, expires 2027-04-01, as an active individual Internet-Draft. The -01 wire model is more specific than a generic aggregate proof:
- Every hop has a WIMSE HTTP Message Signature input tagged `wimse-delegation-chain`.
- Every hop's WIT is carried in the `Workload-Identity-Tokens` Structured Field Dictionary under the same label as that hop's `Signature-Input`; the hop signs the matching dictionary member. A hop must preserve all prior entries and add a unique label for its own WIT.
- In aggregate mode, the message carries `Signature-Aggregate`; the ordinary `Signature` field MUST NOT be present. The verifier reconstructs every signature base from the retained `Signature-Input` entries and the corresponding WIT public keys, then verifies the aggregate against the complete ordered set of key/message pairs.
- Each hop signs a `wimse-req-digest` containing the Content-Digest value it received (or the reserved `origin` marker for the initiator), while `Content-Digest` describes the body it forwarded. The next hop's received digest must match the prior hop's forwarded digest. Responses have the analogous `wimse-resp-digest` lineage.

This authenticates hop participation and body lineage. Method, target URI, query and other HTTP components still depend on the selected WIMSE HTTP Signature covered-component profile. It is not a blanket signature over arbitrary application semantics.

### 29.2 Security property is attribution, not correctness or authorization

A signed hop can deliberately or incorrectly transform the body and still produce a cryptographically valid record of that transformation. The verifier can attribute the transformation to that hop; a separate authorization/policy decision must determine whether it was permitted or semantically correct. The draft expressly leaves authorization out of scope. AEE likewise records execution evidence but does not itself define universal risk classifications or grant authority.

### 29.3 Aggregate-signature deployment gate

The -01 draft is algorithm-agnostic and does not establish a selected production aggregate scheme. Do not implement a custom aggregate primitive. First implement and test individual WIMSE HTTP signatures plus body digest lineage. Add aggregate mode only after selecting an interoperable scheme/profile, pinning key and signer-set encoding, obtaining test vectors, and validating rogue-key/rogue-signer protections and failure behavior. Until then, retain individual hop proofs as the verifiable baseline.

### 29.4 AEE -02 remains an individual SCITT profile draft

The current Datatracker page confirms AEE -02 is an active individual Internet-Draft published November 2026, intended Standards Track, expiring 2027-05-05. It profiles SCITT Signed Statements, hash-chained execution receipts, admission records, cross-operator linked evidence, Registration Policy, offline verification and Bundle requirements. It does not define accreditation, a universal risk taxonomy, an agent identifier scheme or a policy language. KMH must keep these decisions in explicit local governance profiles.

### 29.5 Cross-layer verification matrix

| Layer | What cryptography/evidence establishes | What remains a separate decision |
|---|---|---|
| WIT/WPT | Workload identity and key possession | Authorization for the action |
| WIMSE HTTP Signature | Covered HTTP components from one sender | Semantic correctness of content |
| WIMSE Chain Provenance | Participating hops and body transformation lineage | Whether each transformation was allowed |
| Dialog Binding | Message belongs to a dialog and initiator context | Whether the task itself is permitted |
| SADP | Capability chain and encrypted scoped context release (experimental) | Compliance after plaintext is disclosed; revocation limitations |
| AEE/SCITT | Recorded execution/admission evidence and transparency verification | Universal risk rating or authority grant |

### 29.6 KMH implementation order refined

1. WIT validation and per-hop WIMSE HTTP Signature verification.
2. Exact covered-component profile and request/response Content-Digest lineage.
3. Dialog-context and transaction-token binding.
4. AEE receipt creation for each authorization, transformation, tool call, result and admission.
5. Offline Bundle verification and cross-operator evidence linkage.
6. Experimental aggregate signature adapter only after scheme/profile and vectors are pinned.
7. Independent policy checks for transformation permission, task correctness and context-taint effects.

No aggregate-signature, WIMSE chain, Dialog Binding or AEE cryptographic conformance implementation is claimed by this documentation update.

## 30. WIMSE Agent Evidence Binding -03: credential-to-evidence binding and per-call admission (2026-11-12)

### 30.1 Verified proposal and status

The official Datatracker entry confirms draft-thaha-wimse-agent-evidence-binding-03, last updated 2026-11-01, as an active individual Internet-Draft, intended Informational, expiring 2027-05-05. It is not an adopted WIMSE WG standard or published RFC. It is a companion proposal to AIMS and maps AIMS minimum audit fields to the SCITT Agent Execution Evidence (AEE) profile.

The draft proposes one `aee_evidence` claim in a WIT or another agent token, an in-toto predicate for Execution Receipts alongside an agent audit record, and an `AEE-Caller-Ref` HTTP field linking each serving call to caller-side evidence. It also defines a per-call Serving Party admission procedure.

### 30.2 Credential claim binds agent, policy and evidence discovery

The `aee_evidence` object requires:
- `evidence_service`: issuer identifier for the Evidence Service;
- `policy_pack_digest`: digest of the Policy Pack governing the agent;
- `logical_agent_id`: persistent agent identifier across runtime environments.

Optional members include `transparency_service`, `agent_credential_digest`, `assurance_statement_digest`, `assurance_level` and `assurance_status`. Where `agent_credential_digest` is present, the public key in the Agent Credential Statement must represent the same cryptographic key as the token's `cnf` key; compare represented public keys, not serialized JWK/COSE_Key bytes. Without this optional digest, the claim provides identity/policy correlation but not the stronger credential-key-bound result.

The Evidence Service URI is an identifier and not necessarily a fetchable endpoint. Discovery/retrieval may require deployment configuration or another protocol. Do not assume the claim alone retrieves the evidence.

### 30.3 Per-call admission is distinct from post-hoc evidence verification

The Serving Party makes a decision on every call before acting. It must:
1. Validate the token and request proof-of-possession.
2. Determine applicable Agent Registration and Assurance Statements and check status freshness under local policy.
3. Validate accepted registration authority, assessor/scheme, assurance level and status.
4. Check the Principal and current actor against the operation policy; prior actors in an actor chain are attribution only and must not be used as admission authority.
5. If `AEE-Caller-Ref` is present, recompute `call_digest` from the request received; never trust the caller-supplied digest. Reject mismatch or missing linkage when policy requires it.
6. Apply operation-specific authorization and only then execute.

High-risk operations should check the status list directly when required freshness cannot be established from a signed cached status. An absent revocation entry in a Bundle snapshot proves only the state represented by that snapshot, not current non-revocation. Evidence validation after execution does not replace pre-execution admission.

### 30.4 Actor Chain is attribution, not authority

The draft explicitly warns that prior actors in the `act` chain are informational history. The access-control inputs are the token's top-level claims and current actor. An actor chain is not proof that every hop possessed or attenuated authority. KMH must verify delegated authority independently using the selected delegation profile; never infer permission from a recorded actor chain.

### 30.5 Privacy and identity-linkability

`logical_agent_id` intentionally links one agent across runtime platforms. `AEE-Caller-Ref` exposes the caller's Evidence Service and transaction reference to the Serving Party; actor-chain data reveals participating operators. Natural-person Principals are represented as peppered digests in the referenced AEE profile, not cleartext. KMH needs audience-limited disclosure, retention controls and a documented correlation policy. Do not place raw personal identifiers in evidence claims or public transparency metadata.

### 30.6 KMH integration contract

Add separate interfaces:
- `AgentEvidenceClaimVerifier`: validates claim syntax, issuer, policy digest and logical identity.
- `AgentCredentialBindingVerifier`: verifies optional credential statement digest and public-key equality with `cnf`.
- `AssuranceStatusResolver`: resolves statement and checks status freshness/revocation policy.
- `PerCallAdmissionEngine`: combines identity, current actor, Principal, assurance, requested operation and current policy.
- `CallerEvidenceLinkVerifier`: recomputes call digest at the serving endpoint and verifies AEE-Caller-Ref linkage.
- `LinkedEvidenceVerifier`: validates post-hoc cross-operator evidence bundle and caller/serving receipt linkage.

The runtime should emit distinct records for credential authentication, evidence discovery, assurance status, admission decision, caller digest computation, execution result and linked verification. Do not collapse them into one `trusted=true` flag.

### 30.7 Negative tests

- `aee_evidence` issuer mismatch or unknown Evidence Service;
- wrong policy pack digest or logical agent ID;
- credential statement key differs from WIT `cnf` key;
- stale or revoked assurance status;
- high-risk call uses stale cached status when direct status check is required;
- caller supplies a false `call_digest` or wrong transaction reference;
- AEE-Caller-Ref omitted where policy requires it;
- actor-chain prior agent is mistakenly treated as authority;
- revoked Principal delegation or wrong current actor;
- Bundle snapshot is incorrectly treated as proof of current non-revocation;
- cross-operator receipt references a different call or serving host.

### 30.8 Implementation priority

1. Implement per-call admission and local operation policy first.
2. Add `aee_evidence` parsing and evidence/policy discovery configuration.
3. Bind credential statement public key to WIT `cnf` where required.
4. Implement freshness-aware assurance status resolution.
5. Add server-computed call digest and AEE-Caller-Ref linkage.
6. Produce and verify caller/serving linked evidence receipts.
7. Add in-toto predicate integration and offline Bundle verification.

No AEE claim, admission engine, credential binding, caller-reference or SCITT implementation is added by this research update. No interoperability, conformance or production security claim is made.

## 31. Evidence Binding -03 revision review: key-binding strength, freshness and admission semantics (2026-11-12)

### 31.1 Revision pin and standards status

Pin `draft-thaha-wimse-agent-evidence-binding-03` (November 2026, expires 2027-05-05) for this review. It is an individual Informational Internet-Draft, not an adopted WIMSE WG standard or published RFC. Its IANA claim and HTTP-field registrations are requests, not completed registrations. The proposal is a companion to AIMS and the AEE profile; it does not modify AIMS.

### 31.2 Important distinction: evidence pointer vs credential-key binding

The required `aee_evidence` members (`evidence_service`, `policy_pack_digest`, `logical_agent_id`) provide evidence-service and policy correlation. They do not, by themselves, cryptographically prove that the token's key is the registered key of that logical agent. The optional `agent_credential_digest` enables the stronger credential-key-bound result only when the verifier fetches/verifies the referenced Agent Credential Statement and compares the represented public key to the token's `cnf` key. Compare mathematical public-key values, not serialized JWK/COSE_Key bytes. If this optional binding is absent, KMH must label the result `identity_policy_correlated`, not `credential_key_bound`.

### 31.3 Evidence discovery is not evidence verification

`evidence_service` is an issuer identifier, not necessarily a retrievable URL. `transparency_service`, when included, identifies a service base but not a particular Bundle or evidence period. KMH needs trusted out-of-band discovery/configuration or a defined retrieval profile. A token claim naming an Evidence Service does not prove that the service is honest, that a receipt exists, or that the evidence is valid. Verify the signed statements, issuer, policy digest, registration/assurance chain and transparency inclusion independently.

### 31.4 Per-call admission is pre-execution; linked evidence is post-hoc

For every call, the Serving Party validates token and request proof-of-possession, resolves applicable Agent Registration and Assurance Statements, checks status freshness and accepted issuer/assessor/scheme, evaluates the Principal and current outermost actor against operation policy, recomputes `call_digest` from the received request, enforces caller-reference uniqueness, and emits an admission receipt whether allowed or refused. Only after admission may it execute. Later Linked Verification checks that caller and serving receipts refer to the same call and host. Post-hoc evidence linkage cannot substitute for pre-execution authorization.

### 31.5 Assurance freshness and high-risk operations

The draft permits token-carried assurance level/status as a signed cache only subject to its `status_checked_at` freshness rule. Where policy requires tighter freshness, the Serving Party resolves the status list directly; high-risk operations SHOULD check the status list directly. A Bundle snapshot is historical evidence of the status at its snapshot time, not proof of current non-revocation. KMH must configure operation-specific maximum status age and fail closed when the required freshness cannot be established.

### 31.6 Actor chain semantics

The prior actors in an OAuth `act` chain are attribution only and MUST NOT be used as admission authority. Access-control inputs are the token's top-level claims and current outermost actor. A complete-looking actor chain does not prove that every hop held authority or narrowed it. Verify delegation independently under the pinned delegation profile.

### 31.7 Call digest and gateway limitation

The Serving Party must recompute the call digest over the received request and compare it with the caller's reference; never trust caller-supplied digest. Linked verification checks the serving host and transaction/call reference. The draft identifies a limitation behind shared gateway hosts: if multiple backends share one host, the request-target digest and gateway routing are needed to distinguish them, and a Bundle containing only one admission may not expose wrong-backend admission. KMH must bind the intended backend/service identity in the request profile and record gateway routing/backend identity in serving evidence; do not claim host-only binding distinguishes services behind a shared gateway.

### 31.8 Privacy and correlation

The persistent `logical_agent_id` intentionally enables cross-runtime correlation. `AEE-Caller-Ref` reveals caller Evidence Service and transaction metadata to the serving party. Include these only for intended recipients, use audience-limited evidence distribution, minimize natural-person identifiers, and apply retention controls. Do not expose transparency-service identity if operational privacy policy treats it as sensitive; distribute it out of band instead.

### 31.9 KMH result-state vocabulary

Replace a single `trusted=true` boolean with explicit states:
- `token_authenticated`
- `proof_of_possession_valid`
- `evidence_service_discovered`
- `evidence_signature_verified`
- `credential_key_bound` / `identity_policy_correlated`
- `registration_valid`
- `assurance_status_fresh`
- `delegation_authorized`
- `call_digest_matched`
- `caller_reference_unique`
- `admission_allowed` / `admission_denied`
- `execution_completed` / `execution_failed`
- `caller_serving_link_verified`

Each state records source, profile/revision, timestamp, policy version and failure reason. Missing evidence is `not_established`, never silently converted to success.

### 31.10 Implementation gate

1. Pin and test the -03 claim schema and exact AEE -02 dependencies.
2. Implement evidence-service discovery separately from signature/statement verification.
3. Require credential-key binding for high-risk operations where policy demands it; otherwise preserve the weaker correlation label.
4. Implement operation-specific assurance freshness and direct status checks for high-risk calls.
5. Recompute request digest and bind intended backend identity; add shared-gateway routing tests.
6. Enforce pre-execution admission and emit allow/deny admission receipts.
7. Verify linked caller/serving evidence after execution without treating it as retroactive permission.

No runtime implementation, interoperability test, conformance result or production security claim is made by this documentation update.

## 33. AEE -02 deeper review: Evidence Chain, Decision Points, Epoch roots and offline Bundles (2026-11-12)

### 33.1 Revision pin and status

Pin `draft-thaha-scitt-agent-execution-evidence-02` (November 2026; expires 2027-05-05) for this review. It is an active individual Internet-Draft, intended Standards Track, and is not a published RFC or an adopted SCITT WG standard. The underlying SCITT architecture is RFC 9943; the agent-specific profile remains a proposal.

### 33.2 Evidence Chain scope

AEE defines an Evidence Chain as an ordered sequence of Execution Receipts, each carrying the hash of its predecessor, scoped to one Agent Credential or Serving Party Credential Statement. This means KMH must not assume one global chain for all agents or all services. Maintain independent chains for each scoped credential identity and link chains for a cross-agent Call Chain using Caller References. Credential rotation or a new Serving Party credential requires an explicit chain-continuity/migration policy; do not silently splice unrelated chains.

### 33.3 Decision Points and receipt semantics

An Execution Receipt is produced at a Decision Point in the Harness or Serving Party. KMH should model at least distinct decision points for model call, tool call, delegation, authorization/admission, and execution outcome where the profile requires them. The Serving Party's `admission` receipt records the pre-execution decision for a received call; the caller-side receipt records the caller's corresponding action. A denied request must still produce a denial/admission receipt so the audit chain records the attempted operation and reason. A receipt records what the decision point asserted; it does not independently prove the underlying tool performed the claimed external side effect.

### 33.4 Epoch-root registration and transparency

AEE allows receipts to be registered individually or through an Execution Epoch Statement containing an epoch root. This creates a trade-off: individual registration provides tighter publication latency and per-receipt inclusion, while epoch batching reduces registration overhead but delays transparency until the epoch is closed and registered. KMH must define maximum epoch duration, maximum receipt count/size, closure triggers, crash recovery, duplicate handling, and the behavior when the Evidence Service or Transparency Service is unavailable. High-risk actions may require immediate individual registration or a synchronous inclusion policy; batching must never be described as immediate public transparency.

### 33.5 Bundle and offline verification boundary

AEE Bundle is a self-contained set of Transparent Statements and Execution Receipts sufficient to verify a segment of an Evidence Chain offline. Offline verification proves the integrity and relationships represented in that Bundle and the relevant transparency artifacts; it cannot prove that the Bundle contains the latest status or that no later revocation/assurance change exists. Every offline report must expose the Bundle's evidence period, status observation times, trust anchors, policy versions and freshness limitations. For current high-risk admission, use online status resolution under local policy rather than relying only on an old Bundle.

### 33.6 Cross-operator linking

Caller References link the evidence chains of parties in one Call Chain. Linked Verification must check that both sides refer to the same call, digest, transaction and serving endpoint, and must distinguish correlation from material matching. A matching reference alone does not prove that the requested external effect occurred; compare the serving receipt, execution result, and where needed independent external-system evidence. For shared gateways, bind the intended backend identity and routing decision as specified in Section 31.7.

### 33.7 Evidence service trust and failure policy

The Evidence Service issues Execution Receipts and Execution Epoch Statements and registers them with a Transparency Service. Treat it as a security-critical issuer. Define key custody/rotation, service identity, signing policy, protected persistence, append-only sequencing, recovery and incident response. A failed Evidence Service must not silently turn an otherwise denied action into an allowed one. Define per-operation policy: fail closed for high-risk operations when required pre-execution evidence cannot be durably committed; lower-risk operations may use a bounded local durable queue only if policy explicitly permits and receipts are later reconciled without rewriting history.

### 33.8 KMH implementation sequence

1. Implement a deterministic receipt schema and hash-chain verifier for one credential-scoped chain.
2. Add explicit Decision Point types and allow/deny admission receipts.
3. Persist receipts durably before irreversible high-risk effects, with idempotency and crash-recovery tests.
4. Add individual SCITT registration first; introduce epoch batching only after proving crash-safe epoch closure and documented publication latency.
5. Implement Bundle export/import and offline verification with explicit freshness output.
6. Add Caller Reference linking across two operators and test mismatch, replay, wrong endpoint and omitted-receipt cases.
7. Add Evidence Service key rotation, compromise response, transparency outage and recovery drills.

### 33.9 Required negative tests

- Receipt predecessor hash changed or chain reordered;
- receipt inserted into a chain for the wrong credential;
- duplicate sequence or receipt identifier;
- denied call omitted from evidence;
- crash between receipt persistence, side effect and SCITT registration;
- epoch closed twice, omitted receipt or wrong epoch root;
- stale Bundle misreported as current status;
- caller and serving receipts refer to different body, amount, transaction or backend;
- Evidence Service signing key compromised or rotated without trust update;
- transparency service unavailable during a high-risk call;
- receipt claims an external side effect that independent system evidence contradicts.

No AEE runtime, receipt writer, epoch service, SCITT registration, Bundle verifier or cross-operator integration is implemented by this documentation update. No conformance or production-readiness claim is made.

## 34. AEE -02 newly material controls: configuration integrity, human confirmation and memory boundaries (2026-11-12)

### 34.1 Primary-source status and scope

The IETF Datatracker record checked 2026-11-12 identifies `draft-thaha-scitt-agent-execution-evidence-02`, last updated 2026-11-01, as an active individual Internet-Draft with no formal standing in the IETF standards process. Its November 2026 text expands the profile beyond basic call receipts and linked caller/serving records. This section pins -02; do not assume later revisions preserve the same schema or semantics.

### 34.2 Configuration Integrity Statement (CIS)

AEE -02 defines a Configuration Integrity Statement committing to digests of static agent inputs including system prompts, instruction files, skills, hooks, tool manifests and memory/configuration inputs. It requires mandatory Unicode normalization before digesting textual configuration, and each Execution Receipt references the configuration in force. The profile requires a Decision Point to block a tool absent from the tool manifest committed by the active configuration.

KMH implication: the `FrozenAction` policy check must also verify the active configuration/tool-manifest digest. A tool being registered in code is not sufficient if the current approved manifest does not authorize it. Implement a canonical configuration manifest with explicit file identities, content digests, normalization profile, version, issuer and effective interval. Reject unlisted tools and configuration drift until an authorized re-approval occurs.

### 34.3 Unicode and invisible instruction-injection surface

The draft specifies NFC normalization and treatment of selected invisible/bidirectional code points before digesting textual inputs, including U+200B/U+200C/U+200D, U+2060, U+FEFF, Unicode tag characters U+E0000–U+E007F and bidirectional controls. KMH must vendor the exact -02 normalization profile and test it byte-for-byte; do not improvise a generic “strip invisible characters” function. Preserve original source bytes as protected evidence where required, while calculating the policy digest from the specified normalized representation. Any change to the normalization profile must create a new versioned digest domain.

### 34.4 Human/operator confirmation as a two-record state transition

AEE -02 defines a `confirm` outcome for tool calls requiring Principal/operator approval. The confirmation request and its resolution are distinct receipts. The outcome must refer to the earlier confirmation and match its parent inference, target, request digest and Task. Exactly one outcome is permitted; `allow` is recorded only after confirmation is granted. Refused, missing-at-deadline, unobtainable or operator-halted confirmation resolves to `block`. A Task must not end with unresolved confirmation; if the session closes, the Evidence Service records block before closing the Task. A tool result cannot precede an allow outcome.

KMH implication: implement confirmation as a durable state machine, not a UI boolean. The irreversible tool executor must require a persisted `allow` outcome bound to the exact frozen action digest and Task. Timeout, cancellation, disconnect and operator halt all fail closed and create a denial/block receipt.

### 34.5 Memory boundary and Task lifecycle

AEE -02 defines `memory_digest` at `task_start` and `task_end`, with canonical serialization defined and named by the Harness configuration. This makes cross-task memory changes visible without blocking every call. It does not prove that memory contents are truthful or safe; it commits to a representation. KMH should hash a defined memory snapshot/version at task boundaries, keep raw memory protected, and separately classify provenance/trust of memory entries. Do not put raw memory or secrets in receipts.

### 34.6 Receipt content and decision-point semantics

Execution Receipt request/response digests commit to the octets as seen at the Decision Point. They need not parse the content. Even malformed/error responses must be recorded with the digest of bytes received, or absent if none were received. `response_digest` records what the Decision Point received before the Harness alters, truncates or withholds it; the receipt alone does not prove what the agent was ultimately shown. KMH should separately record any transformation/delivery step and bind the delivered digest where that distinction matters.

### 34.7 Sub-agent identity boundary

The draft distinguishes a Sub-agent declared as part of the parent's capability from an independently registered Logical Agent. A Sub-agent has no Logical Agent identity of its own and acts under its parent's identity; its `subagent_ref` and function must match the governing Agent Credential Statement. KMH must not silently treat a configured sub-agent as an independently trusted principal. If it needs independent identity/authority, register it as a separate logical agent and establish explicit delegation.

### 34.8 Evidence omission and external side-effect limitation

A hash chain cannot record a call for which the Harness emitted no receipt. The draft identifies independent Harness attestation, Serving Party admission receipts and reconciliation of egress receipts against network telemetry as mitigations. A receipt also cannot independently prove that an external side effect actually occurred; corroborate high-impact effects with the external system's own transaction/audit evidence. KMH must state these limits and avoid claims of complete capture based solely on an internal chain.

### 34.9 Privacy and low-entropy digest leakage

A digest of a low-entropy value such as a payment amount on a known endpoint may be guessed and checked by a party holding the receipt. Keep sensitive call details out of public statements, use protected retrieval and audience-limited evidence, and prefer epoch-root registration where the profile recommends reducing individual receipt/digest exposure. Do not treat hashing as anonymization.

### 34.10 Updated KMH implementation gates

1. Implement a versioned Configuration Integrity Statement and canonical tool manifest.
2. Implement exact Unicode normalization/digest test vectors from AEE -02.
3. Make FrozenAction admission require the active approved configuration digest and tool-manifest membership.
4. Implement durable confirmation request/outcome receipts; only explicit allow permits execution.
5. Add task-start/task-end memory digests with a documented canonical snapshot format.
6. Record raw request/response octet digests and separately bind any Harness transformation/delivery.
7. Distinguish declared sub-agents from independently registered agents.
8. Add independent Harness/egress and external-side-effect corroboration for high-risk tools.
9. Add privacy tests for low-entropy digest guessing and public transparency leakage.

No CIS, Unicode normalization verifier, confirmation state machine, memory snapshot hashing, or receipt runtime is implemented by this research update. No conformance or production security claim is made.

## 36. AEE -02 correction and exact Configuration Integrity semantics (2026-11-12)

### 36.1 Correction to Section 34

The primary AEE -02 text distinguishes static behavior-shaping configuration from runtime-written memory. The Configuration Integrity Statement commits to inputs other than the model and policy, and its defined `config-class` values are `system_prompt`, `instruction_file`, `skill`, `hook`, `mcp_config`, `tool_manifest` and `tool_description`. Runtime-written memory is explicitly NOT configuration; it changes within/between Tasks and is committed at Task boundaries through `memory_digest`. Operator-authored seed memory files MAY be treated as `instruction_file` entries. Therefore Section 34's generic phrase “Memory / Configuration Inputs” must not be read as placing all runtime memory in the CIS. The exact model and policy digests are separate AEE commitments, not CIS entries.

### 36.2 Exact canonicalization and digest contract

The `config_digest` is calculated over the canonical CBOR encoding of the ordered `entries` array, or JCS canonical JSON encoding for the JSON form; it is not an arbitrary hash of a concatenated directory or filesystem tree. Entries are ordered by name in octet order. Textual valid UTF-8 content is normalized to Unicode NFC before the selected normalization profile is applied and the resulting UTF-8 octets are digested. Non-UTF-8 content is digested as raw octets. Normalization is for digesting only; the statement does not assert that the Harness also strips characters from the content presented to the model.

### 36.3 Exact normalization profiles

The defined special code points are U+200B, U+200C, U+200D, U+2060, U+FEFF, U+E0000–U+E007F, U+202A–U+202E and U+2066–U+2069. Profile 1 removes them before digesting. Profile 2 rejects the input and issues no statement until corrected. Profile 2 is RECOMMENDED for `system_prompt`, `instruction_file`, `skill` and `tool_description`; do not generalize this recommendation to every binary or configuration class. Preserve source bytes under protected evidence policy if forensic review requires them.

### 36.4 Configuration drift lifecycle

A Configuration Drift Statement records previous and new config digests plus added/modified/removed entries. Drift is an ordinary event; relying-party policy determines its significance. The Harness MUST compute and compare digests at load time and SHOULD re-check them at a bounded interval during a run. A mismatch MUST produce a Drift Statement and a new Configuration Integrity Statement before any further receipt. The relying party SHOULD reject a policy-pack digest change within a Task. A tool absent from the active committed tool manifest MUST be blocked.

### 36.5 Execution Receipt schema precision

The -02 Execution Receipt includes sequence number, previous receipt hash, record type, decision, policy digest, configuration integrity digest, runtime agent identity, Principal, task sequence, optional request/response digests, timestamp, optional per-call agent signature, target, egress host, decision point, confirmation reference, caller identity/reference, admission basis, actor chain, principal link, transaction, task-boundary memory digest, sub-agent reference, delegation reference and call digest. The exact optionality and allowed placement of each field must follow the pinned CDDL; KMH must not invent a superset schema and label it AEE-conformant.

### 36.6 Important additional correction: Evidence Binding revision

The IETF announcement retrieved on 2026-11-12 announces `draft-thaha-wimse-agent-evidence-binding-02` dated 2026-11-01, not -03. The prior sections' claim that -03 was the current published revision is unverified and must be treated as incorrect pending a primary Datatracker record for -03. Pin -02 for this review and inspect the Datatracker revision history before asserting any later version. This announcement describes the claim, in-toto predicate, per-call assurance admission and caller evidence HTTP field as a companion to AIMS; it does not change AIMS.

### 36.7 KMH implementation gates corrected

1. Separate model digest, policy-pack digest, CIS config digest and task-boundary memory digest.
2. Use exact config classes and canonical entries-array encoding; pin CBOR/JCS profile.
3. Implement exact NFC + profile 1/2 rules and test vectors; do not mutate model-visible content merely because digest normalization is applied.
4. Add load-time digest verification and bounded periodic re-check; on drift, issue Drift + new CIS before any further receipt.
5. Enforce active tool-manifest membership at the Decision Point.
6. Validate Execution Receipt fields and optionality against the exact AEE -02 CDDL.
7. Pin Evidence Binding -02 until primary-source revision history confirms a newer revision.

No runtime implementation, conformance test, drift detector, receipt writer or production security claim is made by this documentation correction.
