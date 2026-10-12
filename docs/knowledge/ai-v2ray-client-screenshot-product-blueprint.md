# AI V2Ray Client — Screenshot-Based Product Blueprint v1.0

## Evidence boundary
This blueprint is based on a user-provided Facebook screenshot showing a promotional description and mockup-like UI. It does not establish that the app exists as a working build, that the displayed speed/ping figures are real benchmarks, or that any listed proxy is safe.

## Visible product concepts
- Connection status: Online / Offline
- Latency/ping and download/upload speed indicators
- Active Xray nodes list, sorted by ascending ping
- AI Deep Research / Search & Auto-Tune action
- Use-case selection (examples shown: PUBG, Facebook, streaming, downloads)
- Target app and routing mode
- Configuration export and settings/about screens

## Proposed MVP scope
### P0 — Required for a credible prototype
1. Import one explicitly supported configuration format.
2. Deterministically parse and validate schema; reject unknown or unsafe fields.
3. Show connection state, last test time, latency, and a clear error state.
4. Test a small set of user-consented endpoints with bounded timeouts.
5. Show provenance/source and timestamp for each candidate where available.
6. Provide disconnect, remove configuration, and clear-data actions.
7. Disclose that a working tunnel does not itself guarantee privacy or anonymity.

### P1 — After reliability and safety gates
- Multi-node comparison using repeated latency samples, connection success, packet loss, throughput and stability.
- AI assistance for explaining parse errors or proposing safe normalization, with deterministic validation after any suggestion.
- Export/import with secrets redacted by default.
- Per-app routing only if the chosen core, Android APIs and distribution rules support it and it passes leak testing.

### Defer until verified
- “100% compatible” claims across Xray-core, sing-box, v2rayNG and Clash Meta.
- Guaranteed ping below 100 ms.
- “Clean IP,” “best route,” or privacy/anonymity guarantees without defined measurements.
- Automatic repair of credentials or security-sensitive TLS/SNI/Reality values.
- Public release before security, licensing, privacy and reproducible-build checks.

## Architecture guardrails
- **AI is advisory, not the security authority.** Use deterministic parsers, allowlisted fields and explicit policy checks.
- **Never invent secrets or silently weaken TLS checks.** Do not turn off certificate validation to make a connection work.
- **API keys:** never embed a shared provider key in an APK. If BYO key is supported, explain billing/quota risks, avoid logs, allow deletion/rotation, and use Android secure storage where feasible.
- **Untrusted nodes:** disclose operator/provenance where known and the risks of routing traffic through unknown endpoints. Prefer HTTPS for destination traffic; do not promise that a proxy is trustworthy.
- **Measurements:** display timestamp and test method. Rank using repeated latency, success rate, throughput and stability rather than one ping.
- **Data minimisation:** document telemetry, retention, permissions and whether connection metadata leaves the device.
- **Supply chain:** verify core versions, licences, attribution and signing before bundling.

## Acceptance test matrix
| Gate | Minimum evidence |
|---|---|
| Parse | Valid configs accepted; malformed and unsupported configs safely rejected |
| Connect | Repeated success/failure results with device, network and test time recorded |
| Performance | Multiple samples for median latency, p95 latency, throughput, packet loss and stability |
| Leak safety | DNS and IPv6 leak checks; confirm routing matches selected mode |
| Key safety | No secrets in logs, screenshots, crash reports or repository |
| UX | Clear offline, timeout, invalid config, permission and reconnect states |
| Release | Reproducible build, signed artifact, licence inventory, privacy notice and deletion controls |

## KMH review verdict
**ACCEPT AS A PRODUCT CONCEPT / UI BLUEPRINT. NOT VERIFIED AS A WORKING OR SECURE VPN APP.**
Next step: obtain the repository or APK and run the P0 tests. Do not present mockup metrics as actual test results.
