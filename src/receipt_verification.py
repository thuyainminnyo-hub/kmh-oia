"""Verifier orchestration for the SCITT CCF COSE receipt profile.

Cryptographic COSE verification and CBOR/proof decoding are injected adapters.
This module checks the profile's binding rules; it is not a COSE implementation.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol


VDP_LABEL = 396
INCLUSION_PROOF_LABEL = -1
CONSISTENCY_PROOF_LABEL = -2


class ReceiptVerificationError(ValueError):
    pass


class CoseVerifier(Protocol):
    def __call__(
        self, receipt_bytes: bytes, *, detached_payload: bytes,
        trusted_key_set: Any, expected_service_id: str,
    ) -> bool: ...


class CcfProofCodec(Protocol):
    def decode_receipt(self, receipt_bytes: bytes) -> Mapping[str, Any]: ...
    def decode_inclusion_proof(self, proof_bytes: bytes) -> Mapping[str, Any]: ...
    def validate_inclusion_proof(self, proof: Mapping[str, Any]) -> bool: ...
    def compute_inclusion_root(self, proof: Mapping[str, Any]) -> bytes: ...


@dataclass(frozen=True)
class VerifiedInclusion:
    statement_digest: bytes
    merkle_root: bytes
    transparency_service_id: str
    proof_count: int


class CcfInclusionReceiptVerifier:
    """Validate detached COSE signature and CCF inclusion proof binding."""

    def __init__(
        self,
        *,
        codec: CcfProofCodec,
        cose_verifier: CoseVerifier,
        trusted_key_set: Any,
        expected_service_id: str,
    ) -> None:
        if not expected_service_id or not expected_service_id.strip():
            raise ValueError("expected_service_id is required")
        if trusted_key_set is None:
            raise ValueError("trusted_key_set is required")
        self.codec = codec
        self.cose_verifier = cose_verifier
        self.trusted_key_set = trusted_key_set
        self.expected_service_id = expected_service_id

    def verify(
        self, *, signed_statement: bytes, receipt_bytes: bytes,
    ) -> VerifiedInclusion:
        if not isinstance(signed_statement, bytes) or not signed_statement:
            raise ReceiptVerificationError("candidate Signed Statement must be non-empty bytes")
        if not isinstance(receipt_bytes, bytes) or not receipt_bytes:
            raise ReceiptVerificationError("COSE receipt must be non-empty bytes")

        # RFC 9942 / CCF profile binds inclusion proof data-hash to the digest
        # recomputed from the candidate Signed Statement, never a receipt field.
        statement_digest = hashlib.sha256(signed_statement).digest()
        try:
            receipt = self.codec.decode_receipt(receipt_bytes)
        except Exception as exc:
            raise ReceiptVerificationError("receipt decoding failed") from exc

        if not isinstance(receipt, Mapping):
            raise ReceiptVerificationError("decoded receipt must be a map")
        if receipt.get("payload") is not None:
            raise ReceiptVerificationError("inclusion receipt must use a detached payload")
        unprotected = receipt.get("unprotected_header")
        if not isinstance(unprotected, Mapping) or VDP_LABEL not in unprotected:
            raise ReceiptVerificationError("missing SCITT VDP unprotected header")
        vdp = unprotected[VDP_LABEL]
        if not isinstance(vdp, Mapping):
            raise ReceiptVerificationError("invalid VDP header value")
        proof_blobs = vdp.get(INCLUSION_PROOF_LABEL)
        if not isinstance(proof_blobs, (list, tuple)) or not proof_blobs:
            raise ReceiptVerificationError("receipt must contain inclusion proofs")

        common_root: bytes | None = None
        for proof_blob in proof_blobs:
            if not isinstance(proof_blob, bytes) or not proof_blob:
                raise ReceiptVerificationError("inclusion proof entry must be encoded bytes")
            try:
                proof = self.codec.decode_inclusion_proof(proof_blob)
            except Exception as exc:
                raise ReceiptVerificationError("inclusion proof decoding failed") from exc
            if not isinstance(proof, Mapping) or not self.codec.validate_inclusion_proof(proof):
                raise ReceiptVerificationError("CCF inclusion proof schema validation failed")
            leaf = proof.get("leaf")
            if not isinstance(leaf, Mapping) or leaf.get("data-hash") != statement_digest:
                raise ReceiptVerificationError("proof leaf does not bind candidate Signed Statement")
            try:
                root = self.codec.compute_inclusion_root(proof)
            except Exception as exc:
                raise ReceiptVerificationError("Merkle root computation failed") from exc
            if not isinstance(root, bytes) or not root:
                raise ReceiptVerificationError("computed Merkle root must be non-empty bytes")
            if common_root is not None and root != common_root:
                raise ReceiptVerificationError("inclusion proofs disagree on Merkle root")
            common_root = root

        assert common_root is not None
        try:
            valid_signature = self.cose_verifier(
                receipt_bytes, detached_payload=common_root,
                trusted_key_set=self.trusted_key_set,
                expected_service_id=self.expected_service_id,
            )
        except Exception as exc:
            raise ReceiptVerificationError("COSE signature verification failed") from exc
        if valid_signature is not True:
            raise ReceiptVerificationError("COSE signature or service identity is not trusted")

        return VerifiedInclusion(
            statement_digest=statement_digest,
            merkle_root=common_root,
            transparency_service_id=self.expected_service_id,
            proof_count=len(proof_blobs),
        )
