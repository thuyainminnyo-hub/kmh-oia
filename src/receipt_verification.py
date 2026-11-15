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


def _validate_ccf_protected_header(receipt: Mapping[str, Any]) -> None:
    """Validate the decoded protected-header structure required by CCF -06.

    This is a structural check only. The injected COSE verifier MUST also
    authenticate the protected header as part of the COSE Sig_structure.
    """
    protected = receipt.get("protected_header")
    if not isinstance(protected, Mapping):
        raise ReceiptVerificationError("missing or invalid COSE protected header")
    algorithm = protected.get(1)
    if type(algorithm) is not int:
        raise ReceiptVerificationError("COSE alg protected header must be an integer")
    if type(protected.get(395)) is not int or protected.get(395) != 2:
        raise ReceiptVerificationError("CCF vds protected header must be CCF_LEDGER_SHA256 (2)")


class ReceiptVerificationError(ValueError):
    pass


class CoseVerifier(Protocol):
    def __call__(
        self, receipt_bytes: bytes, *, detached_payload: bytes,
        trusted_key_set: Any, expected_service_id: str,
    ) -> bool: ...


class CcfProofCodec(Protocol):
    """Strict adapter contract.

    Implementations MUST reject malformed CBOR and duplicate map keys before
    returning decoded maps, and MUST validate the complete CCF CDDL schema.
    Python Mapping validation alone cannot detect duplicate keys discarded by
    a permissive decoder.
    """
    def decode_receipt(self, receipt_bytes: bytes) -> Mapping[str, Any]: ...
    def decode_inclusion_proof(self, proof_bytes: bytes) -> Mapping[str, Any]: ...
    def validate_inclusion_proof(self, proof: Mapping[str, Any]) -> bool: ...
    def decode_consistency_proof(self, proof_bytes: bytes) -> Mapping[str, Any]: ...
    def validate_consistency_proof(self, proof: Mapping[str, Any]) -> bool: ...


@dataclass(frozen=True)
class VerifiedInclusion:
    statement_digest: bytes
    merkle_root: bytes
    transparency_service_id: str
    proof_count: int


def data_hash_from_proof(proof: Mapping[str, Any]) -> bytes:
    leaf = proof.get(1)
    if not isinstance(leaf, (list, tuple)) or len(leaf) != 3:
        raise ReceiptVerificationError("CCF leaf must contain three fields")
    data_hash = leaf[2]
    if not isinstance(data_hash, bytes) or len(data_hash) != 32:
        raise ReceiptVerificationError("CCF data hash must be 32 bytes")
    return data_hash


def compute_ccf_inclusion_root(proof: Mapping[str, Any]) -> bytes:
    """Compute the CCF Ledger SHA-256 inclusion root from a decoded CDDL map."""
    leaf = proof.get(1)
    path = proof.get(2)
    if not isinstance(leaf, (list, tuple)) or len(leaf) != 3:
        raise ReceiptVerificationError("CCF leaf must contain three fields")
    internal_hash, internal_evidence, data_hash = leaf
    if not isinstance(internal_hash, bytes) or len(internal_hash) != 32:
        raise ReceiptVerificationError("CCF internal transaction hash must be 32 bytes")
    if not isinstance(internal_evidence, str) or not (1 <= len(internal_evidence.encode("utf-8")) <= 1024):
        raise ReceiptVerificationError("CCF internal evidence must be 1..1024 UTF-8 bytes")
    if not isinstance(data_hash, bytes) or len(data_hash) != 32:
        raise ReceiptVerificationError("CCF data hash must be 32 bytes")
    # CCF permits an empty inclusion path for a one-transaction tree:
    # in that case the leaf hash is already the Merkle root.
    if not isinstance(path, (list, tuple)):
        raise ReceiptVerificationError("CCF inclusion path must be an array")
    h = hashlib.sha256(
        internal_hash + hashlib.sha256(internal_evidence.encode("utf-8")).digest() + data_hash
    ).digest()
    for sibling in path:
        if not isinstance(sibling, (list, tuple)) or len(sibling) != 2:
            raise ReceiptVerificationError("CCF inclusion path elements must have two items")
        left, digest = sibling
        if type(left) is not bool or not isinstance(digest, bytes) or len(digest) != 32:
            raise ReceiptVerificationError("CCF inclusion path requires boolean and 32-byte digest")
        h = hashlib.sha256(digest + h).digest() if left else hashlib.sha256(h + digest).digest()
    return h


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
        _validate_ccf_protected_header(receipt)
        if receipt.get("payload") is not None:
            raise ReceiptVerificationError("inclusion receipt must use a detached payload")
        unprotected = receipt.get("unprotected_header")
        if not isinstance(unprotected, Mapping) or VDP_LABEL not in unprotected:
            raise ReceiptVerificationError("missing SCITT VDP unprotected header")
        vdp = unprotected[VDP_LABEL]
        if not isinstance(vdp, Mapping):
            raise ReceiptVerificationError("invalid VDP header value")
        if set(vdp) != {INCLUSION_PROOF_LABEL}:
            raise ReceiptVerificationError("this verifier accepts inclusion-only receipts; mixed or unknown proof types require consistency verification")
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
            if not isinstance(proof, Mapping) or set(proof) != {1, 2} or not self.codec.validate_inclusion_proof(proof):
                raise ReceiptVerificationError("CCF inclusion proof schema validation failed")
            if data_hash_from_proof(proof) != statement_digest:
                raise ReceiptVerificationError("CCF leaf data-hash does not bind candidate Signed Statement")
            try:
                root = compute_ccf_inclusion_root(proof)
            except Exception as exc:
                raise ReceiptVerificationError("CCF inclusion Merkle root computation failed") from exc
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


def compute_ccf_consistency_roots(
    anchor: bytes, path: list[tuple[bool, bytes]] | tuple[tuple[bool, bytes], ...],
) -> tuple[bytes, bytes]:
    """Fold a CCF SHA-256 consistency proof into (older_root, newer_root).

    Implements Figure 9 of draft-ietf-scitt-receipts-ccf-profile-06.
    Input must already be decoded from the proof's CBOR representation.
    """
    if not isinstance(anchor, bytes) or len(anchor) != 32:
        raise ReceiptVerificationError("consistency anchor must be exactly 32 bytes")
    if not isinstance(path, (list, tuple)) or not path:
        raise ReceiptVerificationError("consistency path must be non-empty")
    older = anchor
    newer = anchor
    for sibling in path:
        if not isinstance(sibling, (list, tuple)) or len(sibling) != 2:
            raise ReceiptVerificationError("each consistency path element must have two items")
        left, digest = sibling
        if type(left) is not bool:
            raise ReceiptVerificationError("consistency path side flag must be boolean")
        if not isinstance(digest, bytes) or len(digest) != 32:
            raise ReceiptVerificationError("consistency sibling digest must be exactly 32 bytes")
        if left:
            older = hashlib.sha256(digest + older).digest()
            newer = hashlib.sha256(digest + newer).digest()
        else:
            newer = hashlib.sha256(newer + digest).digest()
    return older, newer


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
        signed_statement: bytes | None = None,
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
        _validate_ccf_protected_header(receipt)
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
        if INCLUSION_PROOF_LABEL not in vdp and CONSISTENCY_PROOF_LABEL not in vdp:
            raise ReceiptVerificationError("VDP map must contain at least one supported proof type")
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
            if not isinstance(proof, Mapping) or set(proof) != {1, 2} or not self.codec.validate_consistency_proof(proof):
                raise ReceiptVerificationError("CCF consistency proof schema validation failed")

            anchor = proof.get(1)
            path = proof.get(2)
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

            if path[0][0] is not False:
                raise ReceiptVerificationError("first consistency path sibling must be on the right")
            try:
                computed_older, computed_newer = compute_ccf_consistency_roots(anchor, path)
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
        if INCLUSION_PROOF_LABEL in vdp and not inclusion_blobs:
            raise ReceiptVerificationError("inclusion proof array must be non-empty")
        if inclusion_blobs and (
            not isinstance(signed_statement, bytes) or not signed_statement
        ):
            raise ReceiptVerificationError(
                "candidate Signed Statement is required when inclusion proofs are present"
            )
        statement_digest = hashlib.sha256(signed_statement).digest() if inclusion_blobs else None
        for proof_blob in inclusion_blobs:
            if not isinstance(proof_blob, bytes) or not proof_blob:
                raise ReceiptVerificationError("inclusion proof entry must be encoded bytes")
            try:
                proof = self.codec.decode_inclusion_proof(proof_blob)
            except Exception as exc:
                raise ReceiptVerificationError("inclusion proof decoding failed") from exc
            if not isinstance(proof, Mapping) or set(proof) != {1, 2} or not self.codec.validate_inclusion_proof(proof):
                raise ReceiptVerificationError("CCF inclusion proof schema validation failed")
            if data_hash_from_proof(proof) != statement_digest:
                raise ReceiptVerificationError("CCF inclusion data-hash does not bind candidate Signed Statement")
            try:
                inclusion_root = compute_ccf_inclusion_root(proof)
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
