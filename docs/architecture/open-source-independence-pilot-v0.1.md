# KMH OIA — Open-Source Independence Pilot v0.1

**Status:** PHASE 01 — SANDBOX DESIGN / EVIDENCE INTAKE  
**Owner authorization:** 2026-11-03 — scope: all; compute budget: zero; environment: disposable sandbox  
**Production state:** LOCKED — no production, live runtime, customer data, credentials, DNS, deployment, or external service changes authorized  
**Implementation posture:** phone-first; evidence-first; CI verification; QA gate at every phase

## 1. Objective

Evaluate and incrementally implement a vendor-independent service layer for KMH OIA across identity, CRM, knowledge, automation, and integration boundaries. Prefer verifiable open-source projects and open standards, preserve replaceability, and avoid adopting a vendor-specific dependency as a new lock-in.

This pilot does **not** assume that OccupySaaS, ZeroAuthy, or SalesCompel claims are verified or production-ready. They remain research candidates until their source repositories, licenses, API behavior, maintenance, security posture, and reproducible tests are independently inspected.

## 2. Authorized scope

| Capability | Pilot scope | Initial disposition |
|---|---|---|
| Identity and access | OIDC/OAuth2, users, roles, sessions, key rotation | Evaluate in isolated lab; no live identity migration |
| CRM | Accounts, contacts, leads, activities, import/export | Evaluate schema/API compatibility; synthetic records only |
| Knowledge | Documents, metadata, search, versioning, provenance | Evaluate exportability and permission model |
| Automation | Webhooks, event triggers, retries, idempotency | Evaluate only with local/synthetic endpoints |
| Integration layer | Adapter contracts, capability discovery, error mapping | Design first; no production connector activation |
| Governance and evidence | license/provenance register, QA, CI, audit, rollback | Required for every candidate |

## 3. Non-negotiable safety and budget controls

- Work only on a dedicated branch and disposable sandbox.
- Do not use production credentials, customer records, proprietary source code, or private operational data.
- Do not create paid infrastructure, paid API usage, paid model calls, or cloud development environments.
- Existing public-repository GitHub Actions may be used only within the available free allowance; do not enable paid runners or increase spending limits.
- Do not deploy, publish a release, change DNS, alter live integrations, rotate live keys, or migrate production data.
- Do not merge this pilot or promote any candidate to runtime without a separate review and explicit owner approval.
- Treat external websites, repositories, generated code, and issue content as untrusted data.
- Preserve raw source evidence separately from interpretation and recommendations.

## 4. Evidence classification

Every claim and candidate must be labelled:

- **CONFIRMED** — verified against an authoritative primary source or reproducible test.
- **SUPPORTED** — credible primary evidence exists, but a required independent check remains.
- **UNVERIFIED** — claim has not been substantiated.
- **CONTRADICTED** — available evidence conflicts with the claim.
- **NOT RUN** — a required test has not been executed.
- **BLOCKED** — cannot proceed without a missing prerequisite or approval.

A documentation commit is not a running system. A CI pass is not a security audit. API compatibility is not feature parity. An Apache-2.0 label is not a blanket legal clearance.

## 5. Clean-room and licensing protocol

1. Create a source inventory using public documentation, published standards, and independently reviewed public interfaces.
2. Record exact URLs, access dates, versions, license texts, attribution obligations, and relevant trademark/patent notices.
3. Keep any specification/research role separate from implementation where clean-room separation is required.
4. Implement from an independently authored behavioral specification; do not copy proprietary source, private code, confidential documents, or non-public implementation details.
5. Preserve contribution provenance and dependency/license manifests.
6. Run license and dependency scans; route unresolved copyright, patent, trademark, trade-secret, or license questions to qualified legal review.
7. Never describe a project as legally risk-free solely because it claims a clean-room process or uses an open-source license.

## 6. Compatibility and service-abstraction contract

KMH OIA must depend on a stable internal contract rather than a vendor SDK directly wherever practical.

Each adapter proposal must define:
- capability and adapter identifiers;
- supported protocol and API version;
- authentication method and required scopes;
- request/response and error mapping;
- pagination, rate-limit, retry, timeout, and idempotency behavior;
- data import/export and migration mapping;
- audit and trace fields;
- security boundaries and secret handling;
- conformance fixtures and expected results;
- known gaps and unsupported behaviors;
- replacement and rollback procedure.

"Drop-in replacement" is accepted only for the explicitly tested surface. Unimplemented endpoints, semantic differences, extension behavior, and operational constraints must remain visible.

## 7. Phase plan and gates

### Phase 01 — Repository and evidence baseline
- [x] Identify the authoritative KMH OIA repository and read repository instructions.
- [x] Inspect existing architecture, evidence, QA, and CI contracts.
- [ ] Record primary-source evidence for each candidate.
- [ ] Confirm repository branch protection / required checks.
- **Gate 01:** scope, budget, environment, source provenance, and non-production boundary reviewed.

### Phase 02 — Candidate and license intake
- Inventory identity, CRM, knowledge, and automation candidates.
- Verify project ownership, maintenance activity, license, security advisories, release cadence, exportability, and self-hosting requirements.
- Keep OccupySaaS / ZeroAuthy / SalesCompel unverified until direct evidence is obtained.
- **Gate 02:** candidate selection supported by source evidence and license review.

### Phase 03 — Synthetic identity compatibility lab
- Define an OIDC test matrix (discovery, authorization code + PKCE, token validation, JWKS rotation, logout, roles/scopes, negative cases).
- Use synthetic identities and isolated test keys only.
- **Gate 03:** conformance results, security review, and rollback evidence.

### Phase 04 — Synthetic CRM compatibility lab
- Define CRM object and API fixtures; test create/read/update/delete, filtering, pagination, permissions, import/export, and audit history.
- Use synthetic records only.
- **Gate 04:** schema/API coverage, data portability, and negative tests.

### Phase 05 — Knowledge and automation adapters
- Test document metadata, versioning, search, access control, webhook signatures, retries, idempotency, and event traceability.
- Keep all endpoints local or isolated.
- **Gate 05:** data integrity, event integrity, and failure-recovery evidence.

### Phase 06 — KMH OIA integration design
- Map adapters to OIA input gateway, context assembly, workflow, governed tool, state, evaluation, and trace boundaries.
- Keep adapters disabled by default and behind explicit policy.
- **Gate 06:** architecture review, threat model, integration tests, and human approval.

### Phase 07 — Operational readiness proposal
- Produce deployment, backup/restore, monitoring, incident, upgrade, support, and rollback plans.
- Do not deploy as part of this pilot authorization.
- **Gate 07:** readiness evidence reviewed; separate fresh owner approval required before any production action.

## 8. QA and CI requirements

Every phase must retain:
- exact source URLs and retrieval date;
- commit SHA and changed-file list;
- expected vs actual behavior;
- test names, commands, outcomes, and logs/artifacts;
- license/provenance findings;
- risks, gaps, and unresolved questions;
- QA decision: PASS / FAIL / BLOCKED / NOT RUN;
- reviewer and explicit next action.

Existing repository CI is the baseline; do not modify unrelated workflows as part of Phase 01. Review duplicated unit-test execution and required-check configuration separately before proposing CI changes. Do not claim the required-check policy is enforced until repository rules are inspected.

## 9. Baseline repository observations

- Repository: `thuyainminnyo-hub/kmh-oia`; default branch: `main`.
- Baseline main commit inspected: `d96fc7fdcbbed8556da6c4fe499e71553578163e`.
- `AGENTS.md` requires small reviewable changes, exact test reporting, and no unsupported completion claims.
- Existing runtime boundaries include input gateway, OIA core, context assembly, workflow, state, tool security, governed tool execution, evaluation, response, and trace.
- Existing evidence-admission contract distinguishes supplied attestations from trusted source verification and fails closed for learning admission.
- Existing workflows include `test.yml` and `validation.yml`; both currently invoke unit tests in separate jobs/workflows. This duplication is recorded for later CI review, not changed here.
- Baseline GitHub check runs for the inspected main SHA completed successfully at the time of inspection. This is repository baseline evidence only, not evidence for this pilot branch.

## 10. Exit criteria for this document-only phase

Phase 01 may be marked complete only after:
- this plan is committed on an isolated branch;
- a draft PR is opened against the inspected main branch;
- PR CI is observed and all required checks are identified;
- source intake and candidate verification remain explicitly pending until performed;
- no production or live-system changes occur.

**Current decision:** DESIGN IN PROGRESS. No candidate is approved. No software has been installed, executed, integrated, or promoted. Production remains LOCKED.


## 11. Phase 01 CI closeout — 2026-11-03

The pilot commit `95efc324511c5cf6ec5e038715528ad25943fd5c` was re-checked through GitHub Check Runs. Six checks completed successfully:
- `tests` — success
- `performance-evidence` — success
- `repository-validation` — success
- `performance-baseline` — success
- `test` — success
- `deployment-evidence-bundle` — success

This closes the documentation-commit CI check only. It does not demonstrate that any candidate service has been installed, executed, security-tested, or integrated. PR #200 remains open and draft; it is not approved for merge or production promotion.

## 12. Phase 02 — initial public-source and license intake

The following are primary-source findings captured on 2026-11-03. These are intake observations, not final legal opinions, security assessments, or deployment approvals.

| Capability | Candidate | Primary-source finding | Intake disposition |
|---|---|---|---|
| Identity | Keycloak | Project repository identifies Apache-2.0; supports identity and access management | SHORTLIST — inspect deployment, OIDC conformance, operations |
| Identity | authentik | Root LICENSE describes MIT for most code, with enterprise directory and third-party component exceptions; repository describes SAML, OAuth2/OIDC, LDAP, RADIUS | SHORTLIST — map excluded/commercial paths and dependency licenses |
| Identity | ZITADEL | Repository identifies AGPL-3.0 with Apache-2.0 and MIT exceptions in specific directories | HOLD — detailed licensing map required |
| CRM | EspoCRM | Project repository and official download page identify AGPLv3; official page describes self-hosting and REST API | SHORTLIST — assess AGPL obligations, REST coverage, import/export |
| CRM | Twenty | Repository is predominantly AGPLv3 but contains commercial-license files and MIT packages; production restrictions apply to marked commercial files | HOLD — do not assume entire repository is permissively licensed |
| CRM | SuiteCRM | Official documentation identifies AGPLv3; official site describes self-hosted option | SHORTLIST — compare API/data model and operational requirements |
| Knowledge | Docmost | Core is AGPL-3.0; Enterprise directories/features are commercially licensed; official docs describe self-hosted/on-premises options | SHORTLIST — verify exact feature boundary and API/SSO needs |
| Knowledge | AppFlowy | Repository identifies AGPL-3.0 | HOLD — inspect server deployment, component licenses, data export and feature boundary |
| Automation | Activepieces | Core is MIT; enterprise/cloud features and specified directories are under commercial license; official docs recommend Docker Compose with PostgreSQL and Redis | SHORTLIST — restrict test scope to MIT-licensed core |
| Automation | n8n | Official license FAQ describes Sustainable Use License for Community edition and additional commercial-license cases | EXCLUDE from strict OSI-open-source shortlist; possible separate fair-code evaluation only |

### Primary-source references

- Keycloak repository and license: https://github.com/keycloak/keycloak
- authentik root license: https://github.com/goauthentik/authentik/blob/main/LICENSE
- ZITADEL repository/license: https://github.com/zitadel/zitadel
- EspoCRM repository: https://github.com/espocrm/espocrm
- EspoCRM official download/license: https://www.espocrm.com/download/
- Twenty repository license: https://github.com/twentyhq/twenty/blob/main/LICENSE
- SuiteCRM licensing docs: https://docs.suitecrm.com/admin/licensing/
- Docmost editions/license: https://docmost.com/docs/editions
- AppFlowy repository: https://github.com/AppFlowy-IO/AppFlowy
- Activepieces license: https://www.activepieces.com/docs/about/license
- Activepieces installation: https://www.activepieces.com/docs/install/overview
- n8n license FAQ: https://support.n8n.io/article/can-i-use-your-license-for-my-use-case

### Phase 02 evidence gaps

- No source code or release artifact has yet been downloaded, pinned, or scanned.
- No complete SBOM or transitive dependency-license report exists.
- No vulnerability/advisory review has been completed.
- No candidate has been installed or run.
- No API compatibility, data migration, backup/restore, or security test has been executed.
- Free-tier hosting availability and resource requirements are not yet proven. A zero compute budget means use an already available local/disposable environment only; do not provision paid resources.

### Phase 02 QA gate

- Public primary-source/license intake: **SUPPORTED** for the findings above.
- Candidate shortlist: **PROVISIONAL**.
- Legal clearance: **NOT RUN**.
- Dependency/SBOM scan: **NOT RUN**.
- Security review: **NOT RUN**.
- Runtime/compatibility tests: **NOT RUN**.
- Install or deployment approval: **BLOCKED pending environment and resource verification**.
- Production: **LOCKED**.

**Next permitted work:** produce a pinned candidate manifest, verify the exact repository tags/commit SHAs and license files, inspect free local execution options, and prepare synthetic-only conformance fixtures. Do not download or execute candidate code until the sandbox capability and resource budget are confirmed. No merge, release, or production action is authorized.


## 13. Phase 03 — Identity compatibility research (2026-11-04)

### 13.1 Primary-source findings

**Keycloak**
- Official OIDC documentation lists realm discovery at `/realms/{realm}/.well-known/openid-configuration`, authorization, token, userinfo, JWKS/certs, introspection, dynamic registration, and revocation endpoints.
- Keycloak's server administration documentation describes PKCE and allows an administrator to require `S256` for a client. A blank setting does not enforce PKCE; therefore the pilot must explicitly configure S256 rather than assume it is active.
- The official repository identifies Apache License 2.0. This is a favorable baseline license, but transitive dependency licenses still require a complete scan.

**authentik**
- Official documentation lists OIDC/OAuth2 support including authorization code, client credentials, device code, refresh token, token exchange, and PKCE.
- Its default discovery and JWKS paths are application-slug scoped: `/application/o/<slug>/.well-known/openid-configuration` and `/application/o/<slug>/jwks/`. The default issuer is also provider/application-specific. Global issuer mode changes the issuer value but does not move the discovery document to the root URL.
- The repository root license says most code outside `authentik/enterprise/`, `website/`, and specified client-side/third-party exceptions is MIT. Enterprise code and third-party dependencies need separate review; do not treat the entire repository as uniformly MIT.
- Official documentation says JWTs are always signed. With a selected signing key, signatures are asymmetric and public keys are published through JWKS; without one, authentik uses HS256 with the client secret and does not publish an asymmetric JWKS key. The test profile must explicitly select an asymmetric signing key (e.g. RS256) and verify discovery/JWKS.
- Official documentation notes that starting with authentik 2025.10, `email_verified` defaults to `False`. KMH must not infer verified email from the presence of an email claim.

### 13.2 Provisional comparison

| Dimension | Keycloak | authentik | KMH implication |
|---|---|---|---|
| OIDC discovery | Realm-scoped standard path | Application-slug scoped path | Discover dynamically; never hard-code paths |
| Authorization Code + PKCE | Supported; configure enforced S256 | Supported | Test S256 positive and negative cases |
| JWKS | Realm certs endpoint | Provider/application JWKS endpoint | Validate signature, kid, issuer, audience, expiry |
| Introspection/revocation | Documented endpoints | Documented endpoints | Test separately; do not assume identical semantics |
| Issuer | Realm issuer | Per-provider by default; optional global mode | Exact issuer match is mandatory |
| License baseline | Apache-2.0 | MIT core with explicit exceptions | Both require dependency/license inventory |
| Operational footprint | Java service; database/cache topology must be evaluated | Python/Django service; PostgreSQL and worker/outpost topology must be evaluated | No runtime winner without measured local resource evidence |

### 13.3 Provisional disposition

- **Keycloak: PRIMARY COMPATIBILITY BASELINE** for the first OIDC adapter because its documented realm model, endpoint surface, and Apache-2.0 project license provide a clear baseline for a standards-oriented identity service.
- **authentik: SECOND IMPLEMENTATION / DIFFERENTIAL TEST TARGET** because it exposes the same core OIDC building blocks but has meaningful issuer-path, claim-default, signing-key, and license-boundary details that should be tested explicitly.
- This is a research prioritization only. It is not a production product selection, security endorsement, or evidence that either server has passed KMH conformance tests.

### 13.4 Synthetic-only conformance test matrix

All tests below are **DESIGNED / NOT RUN**. Use a disposable local environment only after resource checks. Use synthetic users, synthetic email domains, throwaway client IDs, and ephemeral test keys. No real user records, live secrets, public DNS, or production callbacks.

| ID | Test | Expected acceptance |
|---|---|---|
| ID-01 | Fetch OIDC discovery metadata | HTTPS issuer and required endpoints are present and internally consistent |
| ID-02 | Authorization Code + PKCE S256 | Valid code/verifier succeeds; wrong verifier and missing challenge fail |
| ID-03 | state and nonce | Valid callback succeeds; mismatch/replay is rejected |
| ID-04 | ID token validation | Signature, exact issuer, audience, expiry, nonce, and allowed algorithm validated |
| ID-05 | JWKS rotation | Unknown kid triggers bounded metadata/JWKS refresh; old key overlap behaves as configured |
| ID-06 | UserInfo | Subject is stable and matches ID token subject; scopes gate claims |
| ID-07 | Refresh token | Rotation/reuse/revocation behavior is documented and tested |
| ID-08 | Logout | Front-channel/back-channel support and session invalidation behavior are recorded |
| ID-09 | Roles/groups mapping | Claim names, types, and values normalize to KMH internal permissions without privilege escalation |
| ID-10 | Issuer and redirect mismatch | Wrong issuer, redirect URI, client, or audience fails closed |
| ID-11 | Signing configuration | Asymmetric signature and JWKS verification are mandatory; reject `alg=none` and unexpected algorithms |
| ID-12 | Email verification | `email_verified=false` is not treated as verified identity |
| ID-13 | Introspection/revocation | Client authentication, active state, and error semantics are verified independently |
| ID-14 | Failure/recovery | IdP unavailable, stale JWKS, clock skew, and rate limiting fail safely without bypass |

### 13.5 KMH internal identity adapter contract

Application code must consume a provider-neutral interface, not provider-specific endpoint paths or vendor SDK assumptions:

- `issuer_id` and exact `issuer` allowlist;
- discovery URL and metadata cache with bounded refresh;
- authorization code + PKCE S256 only for the initial browser pilot;
- strict redirect URI allowlist, state, and nonce;
- asymmetric JWT signature verification using discovered JWKS;
- exact `iss`, `aud`, `exp`, `iat`, `nonce`, and `sub` validation;
- normalized identity: `subject_id`, `email`, `email_verified`, `display_name`, `groups`, `roles`;
- explicit mapping of provider claims to KMH permissions; no implicit admin grants;
- safe key rotation, session expiry, logout, revocation, and audit events;
- adapter conformance version and test evidence ID.

Never trust an email address as a stable identity key. Use the validated pair (issuer, subject) as the external identity key. Do not merge accounts across issuers based only on matching email addresses.

### 13.6 Phase 03 QA gate

- Official OIDC endpoint documentation: **CONFIRMED**.
- Keycloak project license declaration: **CONFIRMED** at repository metadata / official project repository.
- authentik license exceptions: **CONFIRMED** from root LICENSE.
- Feature comparison: **SUPPORTED** by vendor documentation; not independently reproduced.
- Version/tag and immutable commit pinning: **NOT RUN**.
- Full dependency/SBOM/license scan: **NOT RUN**.
- Security advisory review: **NOT RUN**.
- Runtime conformance tests ID-01–ID-14: **NOT RUN**.
- Resource and zero-cost sandbox feasibility: **NOT RUN**.
- Production readiness / migration / deployment: **NOT AUTHORIZED**.

### 13.7 Primary sources consulted

- Keycloak OIDC endpoints: https://www.keycloak.org/securing-apps/oidc-layers
- Keycloak PKCE configuration: https://www.keycloak.org/docs/26.3.5/server_admin/
- Keycloak official repository and Apache-2.0 declaration: https://github.com/keycloak/keycloak
- authentik OAuth2/OIDC provider documentation: https://docs.goauthentik.io/add-secure-apps/providers/oauth2/
- authentik root license: https://github.com/goauthentik/authentik/blob/main/LICENSE
- authentik certificate and signing-key documentation: https://docs.goauthentik.io/sys-mgmt/certificates/
- authentik OIDC key-binding / DPoP notes: https://docs.goauthentik.io/add-secure-apps/providers/oauth2/key-binding/

**Current decision:** Phase 03 research and test design are documented. No candidate has been installed or executed. No identity adapter code has been written. Production remains LOCKED.
