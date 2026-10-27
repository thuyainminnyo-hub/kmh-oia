# Cloud Run Staging Acceptance Checklist

Status: **STAGING PREPARATION — NOT DEPLOYED**  
Production decision: **HOLD**

This checklist intentionally keeps cloud spend low while the KMH OIA runtime is being learned, verified, and proven. Passing repository CI does not prove a live Cloud Run deployment or production readiness.

## Verified repository evidence

At the time this checklist was written, the GitHub Actions runs associated with the staging-readiness head commit reported success:

- KMH OIA Tests: run 1018 — test and performance-baseline jobs succeeded.
- KMH OIA Validation: run 937 — repository validation, tests, performance evidence, and deployment-evidence-bundle jobs succeeded.

These are repository/CI results only. They are not proof of a live service, real external provider execution, or production business outcomes.

## Gate 1 — Code and CI

- [x] HTTP adapter, container baseline, and HTTP contract tests are committed on `cloud-run/staging-readiness`.
- [x] Exact-head GitHub Actions tests and validation reported success.
- [ ] Independent code review completed.
- [ ] Local reproducibility confirmed by a developer in the intended environment.
- [ ] Container image build completed and recorded against an immutable commit.

## Gate 2 — Safe staging access

- [ ] Cloud Run service uses authenticated invocation; do not deploy with public unauthenticated access.
- [ ] Authorization is limited to named test identities.
- [ ] Rate/abuse controls and request-size limits are reviewed.
- [ ] Secrets are stored outside source control.
- [ ] Logs exclude request bodies, credentials, and sensitive payloads.
- [ ] Budget alerts and a documented stop/disable procedure are configured.

Note: `/healthz` is a liveness endpoint only. The `/run` handler does not implement application-level authentication. It must not be exposed publicly; authenticated Cloud Run ingress/IAM must be configured and tested before staging use.

## Gate 3 — Runtime proof

- [ ] Deploy to a non-production Cloud Run service with minimum practical resources.
- [ ] Record the service revision and image digest.
- [ ] Verify authenticated `GET /healthz`.
- [ ] Verify authenticated `POST /run` with a synthetic input and capture response plus trace.
- [ ] Verify invalid JSON, missing/invalid content length, wrong content type, empty goal, oversized request, and unknown path fail safely.
- [ ] Confirm logs/trace IDs allow correlation without leaking payloads.
- [ ] Confirm no real external provider call is claimed unless provider identity and outcome are independently evidenced.

## Gate 4 — Persistent data (separate decision)

Do not provision Cloud SQL merely to prove the HTTP adapter works. First demonstrate that the pilot needs durable shared state. Before adding Cloud SQL:

- [ ] Define persistence and replay/idempotency contracts.
- [ ] Add migration tests and integration tests.
- [ ] Estimate instance, HA, storage, backup, and network costs for the chosen region.
- [ ] Test backup restoration and recovery.
- [ ] Obtain an explicit budget approval before creating billable resources.

## Budget rule

Initial goal: keep cloud spend at or below **USD $25–$50 for the first month**, subject to actual pricing and available free tier. This is a target cap, not a guaranteed provider quote. Prefer local execution and CI while gates are incomplete. Configure billing alerts, and remember alerts do not automatically stop spending.

## Promotion decision

Promotion beyond staging requires all applicable gates above to pass and evidence to be attached to the release record. Production remains **HOLD** until security, persistence/recovery, observability, rollback, and real execution evidence are reviewed and approved.
