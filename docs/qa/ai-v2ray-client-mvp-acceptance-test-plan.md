# AI V2Ray Client — MVP Acceptance Test Plan v1.0

## Current status
**PLANNED — NOT EXECUTED.** No repository, APK, or running app was provided for this test plan. Do not mark any test PASS until evidence is captured from an actual build.

## Test device / network record
- Device and Android version:
- App version / build hash:
- Core and version:
- Network type (Wi-Fi/mobile):
- Carrier/region:
- Test date/time:
- Endpoint provenance:
- Tester:

## Test cases
| ID | Test | Procedure | Expected result | Evidence | Status |
|---|---|---|---|---|---|
| P0-01 | Valid configuration | Import a documented supported sample config | Parser accepts it and shows supported protocol | Redacted config + app log | NOT RUN |
| P0-02 | Malformed configuration | Import truncated/invalid schema | Clear error; no crash; no silent repair | Screenshot + redacted log | NOT RUN |
| P0-03 | Unsupported fields | Import config with unknown/security-sensitive fields | Reject or explicitly flag; never silently weaken security | Test config + result | NOT RUN |
| P0-04 | Missing credentials | Import config with required secret removed | Mark invalid; do not invent credentials | Screenshot + log | NOT RUN |
| P0-05 | Connection success | Connect to a test endpoint controlled by tester or explicitly trusted | Connection state reflects actual tunnel state | Timestamped connection log | NOT RUN |
| P0-06 | Endpoint timeout | Use a deliberately unreachable test endpoint | Timeout and recovery are clear; app remains responsive | Screenshot + log | NOT RUN |
| P0-07 | Latency measurement | Repeat health check at least 10 times | Show test time and sample count; don't imply guarantee | Raw measurements | NOT RUN |
| P0-08 | Throughput | Run a controlled speed test with permission | Show method, units, and test conditions | Results + conditions | NOT RUN |
| P0-09 | DNS routing | Compare DNS behavior with tunnel on/off using a test setup | DNS follows selected routing policy; no unexpected leak | Leak-test report | NOT RUN |
| P0-10 | IPv6 routing | Check IPv6 route when enabled/available | No unintended traffic bypass | Leak-test report | NOT RUN |
| P0-11 | Disconnect | Disconnect during active test traffic | Tunnel stops and UI confirms state accurately | Screen recording/log | NOT RUN |
| P0-12 | Secret logging | Inspect app logs/crash reports for API keys/config secrets | No secrets emitted | Redacted log review | NOT RUN |
| P0-13 | Key deletion | Remove BYO API key and restart app | Key no longer usable or present in app storage | Test notes | NOT RUN |
| P0-14 | Data minimisation | Inspect permissions and outbound requests | Only disclosed, necessary data transmitted | Permission and traffic review | NOT RUN |
| P0-15 | Reconnect stability | Repeatedly change network / toggle tunnel | Clear recovery behavior; no false “connected” state | Timestamped test log | NOT RUN |

## Safety requirements
- Test only endpoints you control, have permission to test, or have a legitimate basis to use.
- Redact tokens, UUIDs, passwords, private keys, and other credentials before sharing evidence.
- Do not route sensitive accounts or financial activity through unknown public proxy nodes during testing.
- A successful tunnel or low ping does not prove operator trustworthiness, anonymity, or protection against all data exposure.

## Release gate
A prototype is not release-ready until all P0 cases are executed, critical security findings are fixed, supported protocol/version scope is documented, third-party licences are checked, privacy/data flows are disclosed, and the APK is signed through a controlled process.

## KMH status
**READY FOR TESTING PLAN; BLOCKED ON ARTIFACT.** Next required input: the project repository URL or APK file. After receipt, review the actual artifact and update this matrix with observed results only.
