# AEE-WIRE-01 — AEE -02 Wire Profile Lock

**Profile target:** `draft-thaha-scitt-agent-execution-evidence-02`, November 2026 revision, published 2026-11-01, expires 2027-05-05. This is an active individual Internet-Draft, not an IETF-endorsed RFC or adopted standard.

## Scope
This work implements a deliberately small, fail-closed wire foundation for the AEE Execution Receipt profile:
- Deterministic CBOR decoding/encoding according to RFC 8949 §4.2.1.
- Duplicate map-key rejection before mapping conversion.
- Reject malformed UTF-8, indefinite-length items, non-minimal integer/length encodings, unsupported tags and floating-point/simple values outside the selected profile.
- Compute Execution Receipt record hashes locally from canonical payload bytes, rather than trusting caller-provided hashes.
- Validate a bounded core of Execution Receipt envelope fields and sequence/hash-chain linkage.

## Normative references
- AEE -02 §5: integer-keyed CBOR maps and deterministic encoding per RFC 8949 §4.2.1.
- AEE -02 §5.1: optional JSON representation is I-JSON and RFC 8785 JCS; byte strings are unpadded base64url and digests use named hash algorithm plus value.
- AEE -02 §6.7 / §6.7.1: Execution Receipt and record-hash semantics; SHA-256 over canonical encoding, including key 15 when present; sequence starts at zero with 32 zero octets and increments contiguously.
- RFC 8949 §4.2.1: core deterministic encoding; §5.3.1: duplicate map keys are invalid/indeterminate.
- RFC 8785: JSON Canonicalization Scheme.

## Explicit exclusions
This phase does not implement complete AEE CDDL validation, JSON/JCS encoding, COSE_Sign1 signature verification, credential authorization, SCITT registration, execution epochs, bundles, offline verification, or production integration. The CBOR subset intentionally rejects floats and tags until the AEE CDDL profile's complete permitted value space is implemented and tested. A passing local test suite is not AEE -02 conformance.

## Security boundary
Raw bytes are parsed before a mapping is exposed. Duplicate keys and non-deterministic representations are rejected. Hashes bind the exact canonical receipt bytes but do not establish semantic truth, signer authority, completeness of captured events, or safe behavior.

## Revision discipline
The Internet-Draft may change. Any later revision requires a new profile lock, schema review, updated vectors and explicit compatibility decision. Do not silently track "latest".
