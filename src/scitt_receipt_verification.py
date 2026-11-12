"""Fail-closed orchestration boundary for SCITT COSE receipt verification.

Cryptographic COSE/CBOR and CCF proof verification are deliberately delegated
to a vetted adapter. This module never treats a transparency receipt as proof
that the issuer's underlying claims are true.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class VerifiedCcfReceipt:
    transparency_service_id: str
    verified_statement_digest: str
    verified_signing_key_id: str
    inclusion_verified: bool
    consistency_verified: bool
    tree_size: int | None = None
    tree_root: bytes | None = None


class TrustedTransparencyKeyResolver(Protocol):
    def resolve(self, transparency_service_id: str) -> object: ...


class CcfCoseReceiptAdapter(Protocol):
    def verify(
        self,
        *,
        signed_statement: bytes,
        receipt: bytes,
        trusted_keys: object,
        expected_transparency_service_id: str,
        previously_trusted_tree_root: bytes | None = None,
    ) -> VerifiedCcfReceipt: ...


@dataclass(frozen=True)
class ReceiptVerificationResult:
    verified: bool
    statement_digest: str
    transparency_service_id: str
    signing_key_id: str | None
    inclusion_verified: bool
    consistency_verified: bool
    tree_size: int | None
    tree_root: bytes | None


class ReceiptVerificationError(ValueError):
    pass


def verify_scitt_receipt(
    *,
    signed_statement: bytes,
    receipt: bytes,
    expected_transparency_service_id: str,
    key_resolver: TrustedTransparencyKeyResolver,
    ccf_adapter: CcfCoseReceiptAdapter,
    previously_trusted_tree_root: bytes | None = None,
) -> ReceiptVerificationResult:
    """Verify a CCF-profile receipt against locally computed statement bytes.

    The caller must provision the expected service identity from trusted
    configuration, not from the receipt or an untrusted response.
    """
    if not isinstance(signed_statement, bytes) or not signed_statement:
        raise ReceiptVerificationError("candidate Signed Statement must be non-empty bytes")
    if not isinstance(receipt, bytes) or not receipt:
        raise ReceiptVerificationError("COSE receipt must be non-empty bytes")
    if not isinstance(expected_transparency_service_id, str) or not expected_transparency_service_id.strip():
        raise ReceiptVerificationError("trusted Transparency Service identity is required")
    if previously_trusted_tree_root is not None and (
        not isinstance(previously_trusted_tree_root, bytes)
        or not previously_trusted_tree_root
    ):
        raise ReceiptVerificationError("previously trusted tree root must be non-empty bytes")

    # Hash the exact submitted COSE_Sign1 bytes (including CBOR tag 18).
    statement_digest = hashlib.sha256(signed_statement).hexdigest()
    trusted_keys = key_resolver.resolve(expected_transparency_service_id)
    if trusted_keys is None:
        raise ReceiptVerificationError("no trusted keys configured for Transparency Service")

    verified = ccf_adapter.verify(
        signed_statement=signed_statement,
        receipt=receipt,
        trusted_keys=trusted_keys,
        expected_transparency_service_id=expected_transparency_service_id,
        previously_trusted_tree_root=previously_trusted_tree_root,
    )
    if verified.transparency_service_id != expected_transparency_service_id:
        raise ReceiptVerificationError("receipt Transparency Service identity mismatch")
    if verified.verified_statement_digest != statement_digest:
        raise ReceiptVerificationError("receipt does not bind the exact candidate Signed Statement")
    if not verified.verified_signing_key_id.strip():
        raise ReceiptVerificationError("receipt verification omitted signing key identity")
    if verified.inclusion_verified is not True:
        raise ReceiptVerificationError("receipt inclusion proof was not verified")
    if previously_trusted_tree_root is not None and verified.consistency_verified is not True:
        raise ReceiptVerificationError("receipt consistency with previously trusted tree was not verified")
    if verified.tree_size is not None and verified.tree_size < 1:
        raise ReceiptVerificationError("invalid transparency tree size")
    if verified.tree_root is not None and not isinstance(verified.tree_root, bytes):
        raise ReceiptVerificationError("invalid transparency tree root")

    return ReceiptVerificationResult(
        verified=True,
        statement_digest=statement_digest,
        transparency_service_id=verified.transparency_service_id,
        signing_key_id=verified.verified_signing_key_id,
        inclusion_verified=True,
        consistency_verified=verified.consistency_verified,
        tree_size=verified.tree_size,
        tree_root=verified.tree_root,
    )
