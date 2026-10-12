# AI V2Ray Client — MVP Build / Connect / Run / Verify Gate v1.0

## Gate status
**READY FOR REPOSITORY / APK INTAKE — NOT EXECUTED.**
No source repository, APK, build logs, or test evidence has been provided in this review. Do not mark implementation, connection, security, or release gates PASS until evidence is inspected.

## Scope for first testable increment
Build the smallest safe demonstrator, not a public “AI VPN” release:
1. Android screen for importing a supported configuration.
2. Deterministic schema validation and explicit rejection of unsupported fields.
3. Connection status and actionable error display.
4. Bounded health check and timestamped latency result.
5. Disconnect and delete-config controls.
6. Privacy notice describing unknown proxy operators and metadata exposure.
7. No automatic AI rewriting of credentials, TLS/SNI/Reality fields, or certificate checks.

## Build → Connect → Run → Verify

### 1. BUILD — evidence required
- Repository URL and license.
- Exact Android project/module and dependency/core versions.
- Reproducible build instructions and build output.
- Dependency inventory and licence/attribution review.
- Signed debug/test APK artifact with checksum.
**Exit condition:** the app builds reproducibly and unsupported configs fail safely.

### 2. CONNECT — evidence required
- Explicitly supported protocol/schema documented.
- Test endpoint provenance and permission/terms reviewed.
- Connection attempt logs with secrets redacted.
- Disconnect behavior verified.
- DNS/IPv6 routing and leak-test plan documented.
**Exit condition:** connection success and failure states behave as specified; no secret leakage in logs.

### 3. RUN — evidence required
- Test device, Android version, network type and date/time recorded.
- At least 10 repeated attempts on a controlled test endpoint.
- Record connection success rate, median and p95 latency, packet loss if measurable, throughput, reconnect behavior and battery/data impact.
- Do not present a single ping as a guarantee or as proof of safety.
**Exit condition:** results are reproducible enough to compare builds and failures are documented.

### 4. VERIFY — evidence required
- DNS and IPv6 leak checks for each supported routing mode.
- No API keys or configuration secrets in logs, analytics, crash reports or Git history.
- Clear data/delete configuration behavior tested.
- Permissions and data collection match the privacy notice.
- Third-party core licences, trademarks and distribution policy checked.
**Exit condition:** all critical security checks pass; unresolved critical issues block release.

## Test record template
- Build / commit:
- APK SHA-256:
- Device / Android:
- Network type / carrier:
- Test endpoint provenance:
- Protocol/schema:
- Date/time:
- Attempts / successes:
- Median latency / p95:
- Throughput method/results:
- DNS leak result:
- IPv6 leak result:
- Secret/log scan:
- Disconnect/delete result:
- Known limitations:
- Reviewer:
- Gate result: PASS / FAIL / BLOCKED

## Safety and privacy constraints
- Public proxy nodes are untrusted unless independently assessed; “connected” does not mean “private,” “anonymous,” or “safe.”
- Use HTTPS for destination traffic; do not weaken certificate validation to force a connection.
- Do not store a shared AI-provider key inside the APK. If user-supplied keys are supported, explain provider billing/quota implications, avoid logging, and provide removal/rotation instructions.
- AI may help explain errors or propose non-sensitive normalization, but deterministic validation remains authoritative.
- Never claim a guaranteed ping threshold; performance depends on the user's network, destination, time and endpoint load.

## Next action for the project owner
Provide one of:
- the public repository URL;
- the APK file plus its source repository, if available; or
- the project folder / build instructions.

Until one is provided, the honest state is **BLOCKED — NO ARTIFACT TO TEST**. The blueprint is ready; implementation is not verified.
