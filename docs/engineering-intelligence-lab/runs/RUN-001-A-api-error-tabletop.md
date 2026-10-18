# RUN 001-A — API Error Incident Tabletop

## Run status

- **Run type:** Tabletop simulation only
- **Status:** TABLETOP COMPLETED
- **Live test:** NOT RUN
- **Production PASS:** NOT CLAIMED
- **Environment:** Android-phone-friendly; no live infrastructure or deployment

## Scenario

Fictional post-release incident: HTTP 5xx rate rises from 0.2% to 4.8%, p95 latency from 250 ms to 1.4 s, with downstream dependency timeouts. CPU and memory remain below 70%. The new version receives 25% of traffic. All figures are training data, not real telemetry.

## Decision checkpoints

1. **Contain exposure:** Pause further rollout and inspect metrics, logs, traces, and SLO impact.
2. **Correlate evidence:** Compare release timing with 5xx logs and slow downstream spans. Correlation is evidence, not proof of causation.
3. **Mitigate:** Select a controlled rollback under the incident policy, after checking rollback safety and compatibility.
4. **Verify recovery:** Confirm sustained stability through the agreed recovery window; check SLO metrics, alerts, and dependency health. Keep root-cause investigation open.

## Fictional recovery results

| Metric | Before rollback | After rollback |
|---|---:|---:|
| HTTP 5xx rate | 4.8% | 0.3% |
| p95 latency | 1.4 s | 280 ms |
| Dependency timeout | Frequent | Significantly reduced |
| CPU | 55% | 53% |

The simulated improvement supports investigating a release-related regression but does not conclusively establish root cause.

## Final assessment

- Tabletop checkpoints completed: **4/4**
- Real incident or service recovery: **NOT TESTED**
- Root cause: **SUSPECTED, NOT CONFIRMED**
- Production PASS: **NOT CLAIMED**

## Follow-up actions

- Preserve relevant logs and traces.
- Compare old/new code and configuration, especially the downstream call and timeout behavior.
- Identify and document the specific change before claiming root cause.
- Add a regression test and an appropriate release guard.
- Close a real incident only after the agreed SLO and recovery window are verified; track root-cause work separately.

## Build → Connect → Run → Verify

- **Build:** Run card and scenario prepared.
- **Connect:** Automatic Notion/GitHub sync is not assumed.
- **Run:** Tabletop exercise completed in chat; no live system executed.
- **Verify:** Assessment completed in conversation; verify repository/page after persistence.
