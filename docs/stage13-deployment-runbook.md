# KMH OIA — Stage 13 Deployment & Rollback Runbook

## Scope
Controlled deployment preparation for the deterministic KMH OIA runtime. This runbook defines verification and rollback boundaries; it does not authorize production deployment.

## Pre-deployment gates
1. Confirm release commit is identified and immutable.
2. Run the repository validation workflow.
3. Confirm the full test suite passes.
4. Review performance/load evidence against an explicitly approved target.
5. Confirm security controls required by the deployment environment.
6. Confirm telemetry, alerting, and audit retention are available.
7. Confirm state/memory persistence and recovery strategy.
8. Record deployment approval and rollback owner.

## Deployment boundary
- Deploy only from an approved release commit.
- Use an isolated deployment environment before production.
- Limit external permissions and credentials to the minimum required.
- Keep rollback artifacts for the previous known-good release.
- Monitor health, errors, latency, recovery, and trace continuity during rollout.

## Rollback triggers
Rollback should be initiated when an approved operational threshold is breached, including:
- sustained application errors;
- failed health/validation checks;
- unacceptable latency or resource behavior;
- security-control failure;
- state consistency/recovery failure;
- loss of required observability.

Thresholds must be defined by the deployment owner before release; this repository does not invent production SLO values.

## Rollback procedure
1. Stop further rollout.
2. Preserve logs, traces, metrics, and release identifiers.
3. Route traffic away from the affected release where applicable.
4. Restore the previous approved release artifact.
5. Restore/verify compatible state according to the production persistence strategy.
6. Run smoke and health validation.
7. Verify trace continuity and error rates.
8. Record the incident and rollback result.
9. Do not resume rollout until the failure is reviewed and explicitly cleared.

## Current implementation boundary
The repository currently provides deterministic runtime rollback for local state/memory and bounded recovery for governed tool execution. Operational deployment rollback, durable state recovery, and production telemetry remain deployment-environment responsibilities.

## Release record
- Release commit: TBD
- Deployment environment: TBD
- Approval: TBD
- Rollback owner: TBD
- Production SLOs: TBD
