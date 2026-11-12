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
    def decode_consistency_proof(self, proof_bytes: bytes) -> Mapping[str, Any]: ...
    def validate_consistency_proof(self, proof: Mapping[str, Any]) -> bool: ...
    def compute_consistency_roots(self, proof: Mapping[str, Any]) -> tuple[bytes, bytes]: ...


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



@dataclass(frozen=True)
class VerifiedConsistency:
    older_root: bytes
    newer_root: bytes
    transparency_service_id: str
    proof_count: int
    inclusion_proof_count: int


class CcfConsistencyReceiptVerifier:
    """Verify a CCF consistency receipt against a previously trusted root.

    CBOR decoding, exact CCF schema validation, Merkle folding and COSE
    signature verification are supplied by reviewed adapters. The verifier
    enforces the profile's trust binding and cross-proof root consistency.
    """

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
        self, *, receipt_bytes: bytes, trusted_older_root: bytes,
    ) -> VerifiedConsistency:
        if not isinstance(receipt_bytes, bytes) or not receipt_bytes:
            raise ReceiptVerificationError("COSE consistency receipt must be non-empty bytes")
        if not isinstance(trusted_older_root, bytes) or len(trusted_older_root) != 32:
            raise ReceiptVerificationError("trusted older root must be exactly 32 bytes")

        try:
            receipt = self.codec.decode_receipt(receipt_bytes)
        except Exception as exc:
            raise ReceiptVerificationError("receipt decoding failed") from exc
        if not isinstance(receipt, Mapping):
            raise ReceiptVerificationError("decoded receipt must be a map")
        if receipt.get("payload") is not None:
            raise ReceiptVerificationError("consistency receipt must use a detached payload")

        unprotected = receipt.get("unprotected_header")
        if not isinstance(unprotected, Mapping) or VDP_LABEL not in unprotected:
            raise ReceiptVerificationError("missing SCITT VDP unprotected header")
        vdp = unprotected[VDP_LABEL]
        if not isinstance(vdp, Mapping):
            raise ReceiptVerificationError("invalid VDP header value")
        if not set(vdp).issubset({INCLUSION_PROOF_LABEL, CONSISTENCY_PROOF_LABEL}):
            raise ReceiptVerificationError("unsupported proof type in VDP map")
        proof_blobs = vdp.get(CONSISTENCY_PROOF_LABEL)
        if not isinstance(proof_blobs, (list, tuple)) or not proof_blobs:
            raise ReceiptVerificationError("receipt must contain consistency proofs")

        common_newer_root: bytes | None = None
        trusted_older_root_found = False
        for proof_blob in proof_blobs:
            if not isinstance(proof_blob, bytes) or not proof_blob:
                raise ReceiptVerificationError("consistency proof entry must be encoded bytes")
            try:
                proof = self.codec.decode_consistency_proof(proof_blob)
            except Exception as exc:
                raise ReceiptVerificationError("consistency proof decoding failed") from exc
            if not isinstance(proof, Mapping) or not self.codec.validate_consistency_proof(proof):
                raise ReceiptVerificationError("CCF consistency proof schema validation failed")

            anchor = proof.get("anchor")
            path = proof.get("path")
            if not isinstance(anchor, bytes) or len(anchor) != 32:
                raise ReceiptVerificationError("consistency proof anchor must be exactly 32 bytes")
            if not isinstance(path, (list, tuple)) or not path:
                raise ReceiptVerificationError("consistency proof path must be non-empty")
            if not isinstance(anchor, bytes) or len(anchor) != 32:
                raise ReceiptVerificationError("consistency proof anchor must be exactly 32 bytes")
            for sibling in path:
                if not isinstance(sibling, (list, tuple)) or len(sibling) != 2:
                    raise ReceiptVerificationError("each consistency path element must be a two-item array")
                side, digest = sibling
                if type(side) is not bool:
                    raise ReceiptVerificationError("consistency path side flag must be boolean")
                if not isinstance(digest, bytes) or len(digest) != 32:
                    raise ReceiptVerificationError("consistency path sibling digest must be exactly 32 bytes")
            first = path[0]
            if first[0] is not False:
                raise ReceiptVerificationError("first consistency path sibling must be on the right")

            try:
                computed_older, computed_newer = self.codec.compute_consistency_roots(proof)
            except Exception as exc:
                raise ReceiptVerificationError("consistency Merkle root computation failed") from exc
            if (
                not isinstance(computed_older, bytes) or len(computed_older) != 32
                or not isinstance(computed_newer, bytes) or len(computed_newer) != 32
            ):
                raise ReceiptVerificationError("computed consistency roots must be 32-byte values")
            if common_newer_root is not None and computed_newer != common_newer_root:
                raise ReceiptVerificationError("consistency proofs disagree on newer Merkle root")
            common_newer_root = computed_newer
            if computed_older == trusted_older_root:
                trusted_older_root_found = True

        if not trusted_older_root_found:
            raise ReceiptVerificationError("no consistency proof extends the previously trusted root")

        # A receipt may carry both inclusion and consistency proofs. The CCF
        # profile requires every proof in the VDP map to resolve to one root.
        inclusion_blobs = vdp.get(INCLUSION_PROOF_LABEL, ())
        if not isinstance(inclusion_blobs, (list, tuple)):
            raise ReceiptVerificationError("inclusion proofs must be an array")
        for proof_blob in inclusion_blobs:
            if not isinstance(proof_blob, bytes) or not proof_blob:
                raise ReceiptVerificationError("inclusion proof entry must be encoded bytes")
            try:
                proof = self.codec.decode_inclusion_proof(proof_blob)
            except Exception as exc:
                raise ReceiptVerificationError("inclusion proof decoding failed") from exc
            if not isinstance(proof, Mapping) or not self.codec.validate_inclusion_proof(proof):
                raise ReceiptVerificationError("CCF inclusion proof schema validation failed")
            try:
                inclusion_root = self.codec.compute_inclusion_root(proof)
            except Exception as exc:
                raise ReceiptVerificationError("inclusion Merkle root computation failed") from exc
            if inclusion_root != common_newer_root:
                raise ReceiptVerificationError("inclusion and consistency proofs disagree on Merkle root")

        assert common_newer_root is not None
        try:
            valid_signature = self.cose_verifier(
                receipt_bytes, detached_payload=common_newer_root,
                trusted_key_set=self.trusted_key_set,
                expected_service_id=self.expected_service_id,
            )
        except Exception as exc:
            raise ReceiptVerificationError("COSE consistency signature verification failed") from exc
        if valid_signature is not True:
            raise ReceiptVerificationError("COSE signature or service identity is not trusted")

        return VerifiedConsistency(
            older_root=trusted_older_root,
            newer_root=common_newer_root,
            transparency_service_id=self.expected_service_id,
            proof_count=len(proof_blobs),
            inclusion_proof_count=len(inclusion_blobs),
        )
