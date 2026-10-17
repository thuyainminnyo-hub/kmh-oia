# KMH Research Protocol v1.0

**System:** KMH AI Production Studio  
**Architecture role:** Operating Intelligence Architecture (Brain)  
**Status:** Initial implementation; human review pending  
**Execution constraint:** Android-phone-friendly workflow  
**Control plane:** Notion  
**Versioned artifact:** GitHub repository thuyainminnyo-hub/kmh-oia

## Purpose
Turn AI-assisted research into a reproducible, evidence-led workflow. AI-generated hypotheses are leads to test, not facts to accept.

## Protocol: Question → Hypothesis → Reconstruct → Verify → Decide
1. **Question** — State the exact uncertainty and the decision it affects.
2. **Source inventory** — Prefer primary sources, published standards, original code, and reproducible artifacts. Record dates and links.
3. **Hypotheses** — List plausible explanations and what evidence would falsify each one.
4. **Reconstruction** — Build a minimal, repeatable test. Record inputs, environment, versions, and commands/code.
5. **Verification** — Compare output with the published artifact. Seek an independent implementation or reviewer for security-critical claims.
6. **Evidence classification** — Mark each claim:
   - **Confirmed:** directly reproduced or supported by authoritative primary evidence.
   - **Supported:** credible evidence, but a key independent check remains.
   - **Unverified:** plausible claim without adequate evidence.
   - **Contradicted:** evidence conflicts with the claim.
7. **Limitations** — State explicitly what the evidence does not establish.
8. **Decision** — Recommend an action only proportional to the evidence and risk.
9. **Traceability** — Save source links, test output, commit/version, reviewer, date, and decision.

## Required case-study record
- Title and date
- Research question
- Primary-source URL(s)
- Claim / hypothesis
- Method and environment
- Reproduction steps or code
- Expected vs actual result
- Evidence classification
- Limitations and open questions
- Security / operational impact
- Decision and next action
- Reviewer and verification date

## QA gate
- [ ] Primary source linked
- [ ] Claims separated from interpretation
- [ ] Reproduction steps are specific enough to repeat
- [ ] Actual result captured (never mark PASS without evidence)
- [ ] Independent verification attempted where appropriate
- [ ] Limitations and unresolved questions recorded
- [ ] No secrets, credentials, or private data committed
- [ ] Decision and next action documented

**Gate rule:** If evidence is missing, status remains **Pending / Not Run**, not PASS.

## Example: NIST elliptic-curve seed origins
Primary source: https://www.anthropic.com/research/ecdsa-curve-origins

Anthropic reports that Claude traced most NIST ECDSA curve seed origins to the lrand48 pseudorandom generator initialized with Unix timestamps. The report says this is not a cryptographic break and does not require changing systems. It also leaves open questions: B-163 remains unexplained, the origin of several base points is unknown, and the criteria for skipped candidate curves are not fully known.

**Case-study status (2026-10-17):** KMH executed the published reconstruction logic in the available ChatGPT Python execution environment. All 14 seed strings printed by Anthropic's snippet matched Anthropic's expected output. This is a narrow reproduction of the published calculation; independent review and separate-runtime reproduction remain pending. It was not run on the user's Android device. Do not treat this as proof that every NIST curve or cryptographic system is free of weaknesses.

Verification record: https://github.com/thuyainminnyo-hub/kmh-oia/blob/main/docs/research/runs/nist-ecdsa-seed-reproduction-2026-10-17.md

## Notion ↔ GitHub operating contract
- Notion is the human-readable control record and decision log.
- GitHub is the versioned source for protocol text, scripts, and reproducible artifacts.
- Link the Notion case record to the exact GitHub file/commit.
- A matching document in both services is **not** automatic synchronization. Updates must be made to both until an explicit automation is built and tested.
- Never store API keys or tokens in either document.

## Next implementation steps
1. Review this protocol on a phone.
2. Create a case record for the NIST seed investigation in Notion.
3. Obtain a second reviewer or separate-runtime reproduction of the published seed code.
4. Keep unresolved questions (B-163, unexplained base points, and skipped candidate criteria) visible.
5. Decide whether to automate the Notion/GitHub handoff only after the manual path works.