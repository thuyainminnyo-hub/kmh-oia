# Phase 03.06 — RFC 8785 Canonical JSON for Recovery Plans & Signatures

**Status:** JCS dependency and canonicalization integration committed; latest exact-commit CI is running. Do not mark phase complete until all required jobs pass.
**Date:** 2026-11-10
**Branch:** `phase-02-71/midi-golden-fixtures`

## Research decision

RFC 8785 JCS is the correct serialization profile for JSON objects that are hashed or signed across implementations. It constrains data to I-JSON, uses ECMAScript-compatible primitive serialization, deterministic property sorting and UTF-8 output. It does not perform Unicode normalization. JCS requires JSON numbers to be IEEE-754 compatible; large integers outside the safe integer range must be represented as strings when exactness is required.

Selected Python implementation: `rfc8785` 0.1.4 by Trail of Bits, Apache-2.0, pure Python, no runtime dependencies, API `rfc8785.dumps(value) -> bytes`. The package reports canonicalization errors for invalid input and out-of-domain numeric values.

References:
- RFC 8785: https://www.rfc-editor.org/rfc/rfc8785.html
- RFC 8785 test data / source: https://github.com/cyberphone/json-canonicalization
- Trail of Bits Python implementation: https://github.com/trailofbits/rfc8785.py
- PyPI release 0.1.4: https://pypi.org/project/rfc8785/

## Implementation

- Added `rfc8785>=0.1.4,<0.2` to `requirements-preservation.txt`.
- Added `_canonical_json_bytes(value)` wrapper around `rfc8785.dumps()` with a fail-closed `INVALID_CANONICAL_JSON` error.
- Recovery plan SHA-256 generation now uses JCS bytes.
- Recovery plan digest recomputation now uses JCS bytes.
- Ed25519 approval signature payload now uses JCS bytes; signature excludes only the signature field itself, while algorithm and signing key ID remain signed.
- Added JCS vector coverage for key ordering, float serialization, literals, UTF-8 output, and rejection of NaN/Infinity.

## Compatibility correction from CI evidence

Initial JCS CI failed because POSIX `st_dev`, `st_ino`, and `st_mtime_ns` values were integers above the I-JSON safe integer range. This is expected under RFC 8785; silently rounding them would be unsafe for identity/evidence fields.

Corrected the recovery evidence schema to serialize `device`, `inode`, and `mtime_ns` as exact decimal strings. `mode` remains a small integer. Added regression assertions for these field types. This preserves exact filesystem identity data and makes the plan JCS-compatible.

Commits:
- dependency: `afde00fcaa54a7b9b0e91a57025b4279f9f7cfa8`
- JCS integration: `83acdcd26d85b3294562a2845ceef60cce5a66e3`
- JCS vector tests: `c02219885e21e1b80c1e20db1a756f33adb2136c`
- normalize JCS errors: `e5cb72cf0e93f0582df8ea6fa86f03035e7a53c9`
- Unicode UTF-8 test correction: `0bb670c62e25ff86ed50c0b111eee5de1eecf3e6`
- exact POSIX identity values as strings: `4961ed8c139d9398b36e373879d0373e175eafa1`
- identity schema regression assertions: `3f41679a136e651dc9fe44f7175b666f1b34b1d8`

## CI status at documentation time

- Dependency-only commit `afde00f`: OIA Tests passed (650 tests); MIDI Fixture Integrity passed. This does not validate JCS code.
- JCS integration commit `83acdcd`: workflows were still running at last check.
- JCS test commit `c022198`: OIA Tests failed due to a Python syntax error in a non-ASCII bytes literal; fixed in `0bb670c`.
- JCS code commit `e5cb72c`: OIA Tests/Validation/Preservation Gate A failed because large POSIX filesystem integers exceeded JCS safe integer domain; fixed by converting exact identity values to decimal strings in `4961ed8`.
- Latest commit `3f41679a136e651dc9fe44f7175b666f1b34b1d8`: OIA Tests, OIA Validation, Preservation Gate A and MIDI Fixture Integrity were in progress at last check. Exact final results must be checked before phase acceptance.

## Acceptance criteria

1. Exact latest commit passes OIA Tests and includes JCS tests.
2. Exact latest commit passes OIA Validation, Preservation Gate A on Linux and Windows, and MIDI Fixture Integrity.
3. Add official RFC 8785 Appendix B numeric vectors and Appendix C property sorting vectors, including supplementary-plane Unicode ordering.
4. Confirm canonical plan digest stability across supported Python versions and at least one independent implementation (for example Node.js `canonicalize`).
5. Document all fields that require decimal-string encoding; reject unsafe integer values rather than silently coercing them.

## Security boundaries

- JCS provides deterministic serialization, not authentication, authorization, key management or replay prevention.
- The `rfc8785` Python package is a dependency, not an independent security audit. Pin/hash dependencies and review supply-chain provenance before production.
- Private-key custody, trusted key registry, rotation/revocation, durable atomic nonce store, operator identity integration and recovery transaction ledger remain unimplemented.
- No recovery mutation executor is enabled. PR #217 remains OPEN / DRAFT; no production-readiness claim.