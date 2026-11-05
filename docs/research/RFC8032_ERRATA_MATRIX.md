# RFC 8032 Errata Matrix

**Repository:** thuyainminnyo-hub/kmh-oia  
**Target branch:** feat/nist-curve-parameter-audit  
**RFC:** 8032 — Edwards-Curve Digital Signature Algorithm (EdDSA)  
**Review status:** Initial source-based inventory; implementation and regression tests pending  
**Last reviewed:** 2026-11-06

## 1. Purpose and scope

This document records RFC Editor errata relevant to an EdDSA implementation audit. It separates verified corrections from an item held for a future document update. It is a research and test-planning artifact, not a claim of implementation compliance or cryptographic security approval.

RFC 8032 is an IRTF Informational RFC, not an Internet Standards Track specification. For NIST compliance questions, consult the applicable NIST publications separately.

## 2. Source hierarchy

- Original specification: https://www.rfc-editor.org/rfc/rfc8032
- RFC Editor errata index: https://www.rfc-editor.org/errata/rfc8032
- Informative inline-errata rendering: https://www.rfc-editor.org/rfc/inline-errata/rfc8032.html

The inline-errata rendering explicitly states that it is purely informative and must not be used as a reference. Cite the original RFC and individual RFC Editor errata records in audit findings.

## 3. Verified errata inventory

RFC Editor's errata search currently lists six verified records for RFC 8032:

| Errata ID | Type | Section | Correction summary | Suggested audit treatment |
|---|---|---:|---|---|
| 5519 | Editorial | 5.1.7 | Correct lowercase `s` to uppercase `S` in the scalar range notation. | Documentation/spec transcription check; no algorithm change. |
| 5930 | Technical | 6 | Add the missing `raise` before the bad-signature-length exception in the sample verification code. | If auditing/adapting the sample code, test that invalid signature length actually raises an error. |
| 5968 | Technical | 3.1 | Correct scalar encoding range from `0 < S < L - 1` to `0 <= S <= L - 1`, equivalent to `0 <= S < L`. | Boundary tests: accept 0 and L-1; reject L and values greater than L. |
| 6348 | Technical | 3.4 | Use point-multiplication notation `[2^c]R` rather than `2^c * R` in the group equation. | Mathematical notation/specification consistency review. |
| 6851 | Editorial | 8.7 | Correct acronym `IFU` to `IUF` (Initialize, Update, Finalize). | Documentation/API terminology check; no algorithm change. |
| 8197 | Technical | 5.1.4 | Correct the reference for doubling formulas in Edwards-revisited from Section 3.2 to Section 3.3. | Verify implementation/documentation references the doubling formulas, not dedicated addition formulas. |

Individual authoritative records:

- EID 5519: https://www.rfc-editor.org/errata/eid5519
- EID 5930: https://www.rfc-editor.org/errata/eid5930
- EID 5968: https://www.rfc-editor.org/errata/eid5968
- EID 6348: https://www.rfc-editor.org/errata/eid6348
- EID 6851: https://www.rfc-editor.org/errata/eid6851
- EID 8197: https://www.rfc-editor.org/errata/eid8197

## 4. Held erratum — not a verified correction

| Errata ID | Status | Section | Summary | Audit treatment |
|---|---|---:|---|---|
| 7031 | Held for Document Update | 7.1 | Proposes adding 12 additional edge-case test vectors. | Track as supplemental test material; do not label it a verified correction or normative requirement. |

Authoritative record: https://www.rfc-editor.org/errata/eid7031

The held status must remain distinct from Verified. Do not silently treat proposed additional vectors as an adopted change to RFC 8032.

## 5. Minimum regression-test plan

The following are proposed tests. They have **not** been implemented or executed as part of this commit.

| Test ID | Requirement | Expected result |
|---|---|---|
| ED-ERR-5930-01 | Verification called with a signature of invalid length | Reject/raise the documented error; must not continue silently. |
| ED-ERR-5968-01 | Scalar boundary `S = 0` | Accept as within the specified range, subject to the relevant verification context. |
| ED-ERR-5968-02 | Scalar boundary `S = L - 1` | Accept as within the specified range. |
| ED-ERR-5968-03 | Scalar boundary `S = L` | Reject. |
| ED-ERR-5968-04 | Scalar `S > L` | Reject. |
| ED-ERR-6348-01 | Group-equation implementation/spec review | Confirm point multiplication is interpreted consistently with RFC 8032 Section 2 notation. |
| ED-ERR-8197-01 | Doubling-formula reference review | Confirm the cited Edwards-revisited section is 3.3 (Dedicated Doubling). |
| ED-ERR-7031-01 | Review proposed additional vectors | Record separately as held/supplemental; do not claim RFC-mandated adoption. |

The boundary cases above are specification-derived test cases, not proof that any particular implementation passes them. For EdDSA verification, apply the complete algorithm and its validation rules; do not infer that accepting a scalar encoding alone makes a signature valid.

## 6. QA and evidence rules

- Preserve the exact RFC Editor errata status and source URL for every finding.
- Keep editorial and technical errata distinguished.
- Keep Verified and Held records distinguished.
- Record test code, runtime, dependency versions, command, commit SHA, and complete test output.
- Mark unimplemented tests as `PENDING`; unexecuted tests must never be marked `PASS`.
- A passing RFC vector suite does not establish side-channel resistance, secure key management, production readiness, or absence of cryptographic weaknesses.
- This matrix does not establish NIST compliance. NIST SP 800-186 and FIPS 186-5 require a separate standards/errata review.

## 7. Current disposition

**Research inventory:** Recorded in this file.  
**Regression tests:** Planned, not implemented.  
**Execution evidence:** Not yet produced for this matrix.  
**Independent review:** Pending.  
**Merge / production approval:** Not granted by this document.

Next step: implement the narrowly scoped regression tests on this branch, run them in CI, capture exact commit and workflow evidence, and obtain independent review before proposing a pull request.
