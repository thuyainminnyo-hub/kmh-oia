# RUN 001 — Cloud Native နဲ့ DevOps

- Parent project: KMH Engineering Intelligence Lab
- Source: https://harryyan.uk/article59.html
- Source evidence: full article text pasted by the user into the ChatGPT conversation on 2026-10-18.
- Device constraint: Android phone only; no assumed computer, CLI, Kubernetes cluster, cloud account, or paid resources.
- Run type: Read-and-analyze; non-production.
- Status: ARTICLE REVIEW COMPLETE; TECHNICAL EXPERIMENT PENDING; VERIFICATION PENDING.

## Core thesis

Cloud-native tooling grew out of the need to operate software systems through software, align development and operations around service outcomes, observe production behavior, automate repeatable actions, and make change safer. Cloud infrastructure helped accelerate the movement, but cloud-native practice is not simply a synonym for using a cloud vendor.

## Claims and reasoning extracted from the article

1. Development and operations can have conflicting incentives. Shared service-level objectives help align decisions around customer-facing reliability.
2. SLOs and error budgets provide a framework for balancing reliability work and feature delivery.
3. Observability needs multiple signal types:
   - Metrics: quantify rates, latency, resource use, and errors.
   - Logs: provide event-level details.
   - Traces: follow requests across service boundaries.
4. CI/CD and automated checks can detect quality/security issues earlier and repeat the checks consistently.
5. Progressive delivery and rollback/roll-forward practices reduce the blast radius of changes.
6. Containers, orchestration, autoscaling, and infrastructure as code can make operations more repeatable, but introduce their own complexity and operational requirements.
7. Tool choices should follow the system's needs; the listed ecosystem is a menu of examples, not a requirement to install everything.

## Important technical qualifications

- SLA is an external/service commitment; SLO is an internal target; error budget is the tolerated unreliability implied by an SLO over a defined window. The actual calculation depends on the SLI, window, and policy.
- CAP is commonly simplified as a choice of two out of three. More precisely, when a network partition occurs, a distributed system must trade off strong consistency against availability for the affected operations; partition tolerance is the assumed fault condition, not a freely selectable feature.
- Monitoring alone does not guarantee self-healing. Automated remediation needs safe thresholds, bounded actions, idempotency where possible, permissions, alerting, and a tested recovery path.
- Kubernetes, a service mesh, distributed tracing, and multi-tool observability are not automatically justified for a small project. Start with the simplest architecture that meets measurable needs.
- Progressive delivery and GitOps are related but distinct: rollout controllers govern release progression; GitOps controllers reconcile declared desired state. Exact responsibilities depend on the chosen products and setup.
- The article's named tools are examples, not evidence that any of them are installed or configured in the KMH environment. No deployment or integration was performed in this run.

## Proposed phone-friendly follow-up experiment

Create a paper/design-only incident scenario; do not deploy anything:
- Scenario: a hypothetical API's 5xx error rate rises after a release.
- Expected signals: request rate, error rate, latency, CPU/memory, relevant logs, and trace spans if distributed calls exist.
- Decision flow: alert → inspect dashboard/logs → compare with SLO/error budget → pause progressive rollout or rollback according to an explicit policy → verify recovery.
- Record expected vs actual only after a real test; until then actual result is "Not run".

## Evidence and outcome

- Evidence source: user-pasted article text in conversation; source URL recorded above.
- Actual result: article claims and caveats summarized; no software execution performed.
- Article-analysis status: COMPLETE.
- Technical experiment status: PENDING.
- Verification status: PENDING.
- PASS/FAIL: NOT ASSIGNED — no executable test or observed system result.
- Next action: use the scenario to draft a minimal observability/incident-response Run Card, then decide whether a no-install simulation is feasible on Android.

## Safety gate

Do not paste credentials, tokens, or personal secrets into Notion/GitHub. Do not run commands, deploy services, or create paid cloud resources until permissions, cost, rollback, and scope are explicit.
