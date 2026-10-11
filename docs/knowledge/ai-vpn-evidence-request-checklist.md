# AI VPN Project — Evidence Request & Owner Follow-up Checklist v1.0

## Purpose
Convert the screenshot-based review into a concrete request for the project owner. This is a review checklist, not a claim that the APK or source code has been inspected.

## Evidence to request from the owner
### A. Project identity and provenance
- Official project name and official distribution page
- Public source repository URL, if available
- Maintainer/contact and release version
- Build date and APK SHA-256 checksum
- Signing certificate fingerprint and how updates are verified

### B. Build and implementation
- Source code or reproducible build instructions
- Supported Android versions and required permissions
- Exact core versions and protocol schema test matrix
- Third-party components, licences, and attribution
- Whether the app routes all traffic or only selected applications

### C. Security and privacy
- Data-flow diagram: app, AI provider, backend, proxy endpoints, logs
- Where a Gemini API key is stored and whether it is ever sent to a backend
- Confirmation that secrets are never logged or embedded as a shared key
- DNS and IPv6 leak-test results; reconnect and kill-switch behavior if offered
- Privacy policy, data retention, and endpoint-provenance disclosure
- Known limitations and threat model for public proxy nodes

### D. Performance evidence
- Timestamp and location/network used for each test
- Ping methodology and sample count
- Median and p95 latency, download/upload throughput, packet loss
- Connection success rate and test duration
- Test destinations and whether numbers are measured or illustrative
- Repeated tests during peak and off-peak periods

### E. Release/distribution
- Release signing and integrity verification
- Update channel and vulnerability reporting process
- F-Droid metadata/build reproducibility status if F-Droid is claimed
- Current Play Store policy review if Play Store distribution is planned
- Support contact and user-facing uninstall / data deletion instructions

## Owner message template
Hello, I saw the AI VPN / V2ray client concept and would like to review it fairly before recommending it. Could you share the official project/repository link, release version, APK SHA-256 and signing information, and any reproducible tests for connection reliability, latency/speed, DNS/IPv6 leaks, and API-key handling? Please also clarify which metrics in the screenshots are live measurements versus demo values, how proxy sources are vetted, and where user/API-key data is sent or stored. I will treat the project as unverified until these details are available. Thank you.

## Review gate
- **Gate 0 — Identity:** official project source and owner are attributable.
- **Gate 1 — Integrity:** APK signature/checksum and update channel are explainable.
- **Gate 2 — Function:** reproducible connection and performance tests exist.
- **Gate 3 — Security:** secret handling, DNS/IPv6, endpoint risk and data flow are reviewed.
- **Gate 4 — Release:** licence, privacy, distribution and support are documented.

## Current state
**PENDING OWNER EVIDENCE.** The screenshot provides a UI concept only. Do not enter a real API key, route sensitive traffic, or rely on the service for privacy-critical use until trust and security are established.
