# OpenSSL FIPS 140-3 EdDSA Classification Note

**Repository:** thuyainminnyo-hub/kmh-oia  
**Branch:** feat/nist-curve-parameter-audit  
**Scope:** OpenSSL FIPS Provider certificate #4985 and EdDSA classification  
**Status:** Source-reviewed note; no KMH OIA runtime operation tested  
**Reviewed:** 2026-11-06

## 1. Executive finding

For OpenSSL FIPS Provider certificate #4985, Ed25519 and Ed448 are listed as non-approved services in the module's non-proprietary Security Policy (Table 13, Non-Approved Services). Their presence in OpenSSL EVP/provider documentation must not be interpreted as FIPS-approved service status under certificate #4985.

NIST CMVP currently lists certificate #4985 as Active, FIPS 140-3, overall Level 1, with sunset date 2030-03-10. The certificate's active status does not change the non-approved classification of Ed25519 and Ed448 in its Security Policy.

## 2. Primary evidence

1. NIST CMVP certificate #4985: https://csrc.nist.gov/projects/cryptographic-module-validation-program/certificate/4985
   - Certificate status: Active.
   - Standard: FIPS 140-3.
   - Module: OpenSSL FIPS Provider.
   - Sunset date: 2030-03-10.
   - Approved algorithm list includes ECDSA services.
2. OpenSSL FIPS 140-3 Non-Proprietary Security Policy for certificate #4985: https://csrc.nist.gov/CSRC/media/projects/cryptographic-module-validation-program/documents/security-policies/140sp4985.pdf
   - Table 13, Section 4.4 (Non-Approved Services), lists Ed448 and Ed25519 under signature generation or verification.
3. OpenSSL FIPS Provider documentation: https://docs.openssl.org/3.6/man7/OSSL_PROVIDER-FIPS/
   - Provider capability/algorithm availability and FIPS approval are distinct.
   - The `fips=yes` property is required for FIPS-compliant fetches.
   - An algorithm's operation-level approval must be evaluated; a missing indicator must not be interpreted as approval.
4. OpenSSL EdDSA EVP documentation: https://docs.openssl.org/3.4/man7/EVP_SIGNATURE-ED25519/
   - Describes Ed25519, Ed25519ctx, Ed25519ph, Ed448 and Ed448ph instances.
   - This documents API capability, not approval under CMVP certificate #4985.

## 3. Classification matrix

| Item | Classification / evidence | Audit treatment |
|---|---|---|
| Certificate #4985 | Active FIPS 140-3 certificate; sunset 2030-03-10 | Verify deployed module version and operational environment against certificate scope |
| Ed25519 signature service | Non-approved service in Security Policy Table 13 | Must not be reported as FIPS-approved under #4985 |
| Ed448 signature service | Non-approved service in Security Policy Table 13 | Must not be reported as FIPS-approved under #4985 |
| ECDSA | Approved algorithm services are listed by CMVP, subject to certificate conditions and approved mode | Verify curve, key size, operation, module version and indicator |
| EVP EdDSA API availability | API capability described by OpenSSL | Do not infer CMVP approval from API availability |
| Runtime `fips-indicator` | Operation-level evidence where applicable | Record actual result; missing indicator is not PASS |

## 4. Required implementation and QA controls

- Keep RFC 8032 compatibility tests separate from FIPS compliance tests.
- Record OpenSSL library version, FIPS module version, provider identity, configuration, property query, module integrity/self-test state and operating environment.
- For Ed25519/Ed448, report RFC compatibility results separately and classify certificate #4985 service use as non-approved.
- For ECDSA, do not assume approval solely because the algorithm appears in the certificate list; verify the approved curve, key size, operation, module configuration, certificate scope and operation indicator.
- A provider fetch or successful signature operation is not sufficient evidence of FIPS approval.
- Do not claim the KMH OIA runtime is FIPS validated without matching its exact deployed module and operating environment to the certificate's validated scope.

## 5. Test plan (not yet implemented or executed)

| Test ID | Test | Expected evidence |
|---|---|---|
| FIPS-ED-001 | Confirm certificate #4985 identity and active status | NIST CMVP record snapshot/date |
| FIPS-ED-002 | Confirm Ed25519 / Ed448 classification | Security Policy Table 13 reference |
| FIPS-ED-003 | Inspect deployed OpenSSL and FIPS module versions | Runtime inventory |
| FIPS-ED-004 | Record provider identity and property query | Runtime diagnostic output |
| FIPS-ED-005 | Run RFC 8032 vectors independently of FIPS claim | Vector output, explicitly labelled compatibility |
| FIPS-EC-001 | Check ECDSA approved-mode conditions | Curve/key/operation evidence and indicator |
| FIPS-EC-002 | Validate module/operational-environment match | CMVP certificate scope evidence |

All tests above are **PENDING** until code is implemented and execution evidence is captured.

## 6. Disposition

**Research classification:** Source-reviewed.  
**KMH OIA runtime validation:** Not performed.  
**FIPS compliance claim for Ed25519/Ed448 under certificate #4985:** Not allowed; Security Policy classifies them as non-approved services.  
**ECDSA FIPS status:** Conditional; verify exact approved parameters and operational conditions.  
**Independent review:** Pending.  
**Merge / production approval:** Not granted by this note.
