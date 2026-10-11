# Case Study: AI-Assisted Free VPN / Proxy Selector — Architecture Review v1.0

## Status
**Decision: ACCEPT WITH MAJOR SECURITY AND FEASIBILITY REFINEMENTS.**
This review is based on the user-provided project description only. No source code, APK, build, server telemetry, or independent benchmark was supplied or inspected.

## Product concept
An Android-first free VPN/proxy helper that asks the user what they want to do (e.g., social media, gaming, video), discovers public proxy configurations, validates and ranks candidates for a Southeast Asia/Myanmar route, then lets the user import/connect with minimal manual configuration.

## Proposed components from the draft
- Client: Android app; compatibility goals mention Xray-core v1.8.24, sing-box, v2rayNG and Clash Meta.
- Discovery: public Telegram channels, GitHub repositories/raw subscriptions, public CDN/Cloudflare Workers proxy sources.
- AI: Gemini-based researcher / web-digging agent to normalize or repair malformed configuration candidates.
- User flow: obtain an AI API key if required, choose use case, generate/import configuration, connect.

These are **proposed design claims**, not verified capabilities. “100% compatible,” “AI can repair keys,” and “ping under 100 ms” need reproducible technical evidence.

## Main engineering findings

### 1. A valid configuration is not necessarily a working or safe proxy
Syntax repair can normalize a known schema, but cannot reliably recover missing credentials, prove that a server is operational, or establish that an endpoint is trustworthy. Separate:
- parse/schema validation;
- endpoint reachability;
- TLS/handshake validation;
- latency and throughput tests;
- route-specific application tests;
- trust and abuse screening.

### 2. Public proxy discovery creates material security risk
Public configurations may be dead, misconfigured, monitored, modified, or operated by hostile parties. A VPN/proxy operator may observe connection metadata and, depending on protocol and endpoint handling, unencrypted traffic. HTTPS protects content in transit to the destination but does not make the proxy operator inherently trustworthy. Do not promise anonymity or privacy solely because a tunnel connects.

### 3. AI must not be the security authority
Use deterministic parsers, schema validation, allowlisted protocol fields, and policy checks as the source of truth. AI can suggest normalization, explain errors, or rank candidates using explicit metrics, but it must not invent credentials, silently rewrite security-sensitive TLS/SNI/Reality fields, disable certificate checks, or label an endpoint “safe” without evidence.

### 4. API key handling needs redesign
Avoid asking users to paste a personal Gemini API key into an untrusted client unless they understand the cost and abuse risks. A key embedded in an APK is extractable. If users provide their own key, store it only with platform secure storage where feasible, never log it, support deletion/rotation, and explain provider billing/quotas. A backend proxy protects a provider key but introduces operating cost, abuse prevention, and privacy obligations. Never expose a shared backend key in client code.

### 5. “Free” has an operating cost
Public nodes can disappear or become saturated. AI calls, monitoring, backend bandwidth, abuse prevention, signing, distribution, and maintenance all have costs. Publish a realistic free-tier policy and avoid implying guaranteed uptime or speed.

### 6. Performance claims require measurements
“Ping below 100 ms” cannot be guaranteed across users, networks, time, and destinations. Select by live measurements from the user's actual network and intended destination. Track median and p95 latency, connection success rate, download/upload throughput, packet loss, and stability over time. Label results with test time and sample size.

### 7. Protocol and distribution scope should be narrowed for MVP
Do not claim simultaneous 100% compatibility with multiple cores until the exact schema mapping and test matrix pass. Pick one Android integration path and a limited set of supported protocols for the first release. Validate licensing, attribution, and distribution requirements for bundled third-party components. Play Store and F-Droid requirements should be checked against current policies before choosing distribution.

## Recommended MVP
1. **User intent:** select general use case; explain that this helps rank performance, not bypass destination-specific restrictions or guarantee privacy.
2. **Candidate intake:** use a small, documented source allowlist; record provenance, timestamp, protocol, and licence/terms where applicable.
3. **Deterministic validation:** parse only supported schemas; reject unknown or unsafe fields; never invent secrets.
4. **Safe connection testing:** perform bounded health checks and disclose what is tested. Do not test or route other people's traffic without permission.
5. **Ranking:** use measured latency, stability, throughput, freshness, and risk flags; avoid a single ping-only score.
6. **Consent and transparency:** show endpoint operator/provenance when known, data exposed, limitations, and a clear disconnect/delete action.
7. **QA:** security review, reproducible tests, crash tests, battery/data use, privacy review, and signed APK release.

## Threat model / QA checklist
- Malicious or compromised proxy node
- Configuration injection and parser exploits
- API-key theft, billing abuse, or logs containing secrets
- DNS leaks, IPv6 leaks, and traffic escaping the tunnel
- Permission overreach, unexpected data collection, or unclear retention
- Stale/revoked endpoints and misleading latency tests
- Supply-chain and licence issues in bundled cores
- User confusion between “connected,” “fast,” “private,” and “anonymous”

## Claims that must be softened until proven
- “100% compatible” → “supports the listed tested formats/versions.”
- “AI repairs broken keys” → “AI may propose normalization for supported schemas; invalid credentials and unreachable servers cannot be repaired by formatting.”
- “Best clean IP / SNI / TLS Reality” → explain measurable selection criteria and do not equate “clean” with trusted.
- “Ping below 100 ms” → “selects candidates that measured below the configured threshold at test time, where available.”
- “Free” → disclose limits, costs, data policy, and sustainability.

## Verdict
**ACCEPT WITH MAJOR REFINEMENTS as a prototype concept. NOT VERIFIED as a secure, performant, or production-ready VPN.**
The next gate is an architecture threat model and a small testable MVP—not marketing claims. Do not connect users to arbitrary AI-generated endpoints without deterministic validation and explicit risk disclosure.

## Evidence needed for the next review
- Repository and source code
- APK or reproducible build instructions
- Exact protocol schemas and supported-version test matrix
- Endpoint provenance and selection algorithm
- Privacy policy / data-flow diagram
- API-key storage and logging design
- Test results for latency, throughput, failure rate, DNS/IPv6 leak checks, and reconnect behavior
- Third-party licence and distribution review
