"""Fail-closed AEE -02 wire primitives.

This module implements a restricted deterministic-CBOR subset and the
Execution Receipt record-hash primitive. It is not a complete AEE CDDL,
JCS, COSE, credential, SCITT, or bundle verifier.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


ZERO_HASH = b"\x00" * 32
MAX_DEPTH = 64
MAX_ITEMS = 100_000
MAX_BYTES = 16 * 1024 * 1024


class AeeWireError(ValueError):
    """Malformed or unsupported AEE wire representation."""


def _head(major: int, value: int) -> bytes:
    if value < 0:
        raise AeeWireError("CBOR argument must be non-negative")
    prefix = major << 5
    if value < 24:
        return bytes((prefix | value,))
    if value <= 0xFF:
        return bytes((prefix | 24, value))
    if value <= 0xFFFF:
        return bytes((prefix | 25,)) + value.to_bytes(2, "big")
    if value <= 0xFFFFFFFF:
        return bytes((prefix | 26,)) + value.to_bytes(4, "big")
    if value <= 0xFFFFFFFFFFFFFFFF:
        return bytes((prefix | 27,)) + value.to_bytes(8, "big")
    raise AeeWireError("integer exceeds CBOR uint64 range")


def deterministic_cbor_encode(value: Any, *, _depth: int = 0) -> bytes:
    """Encode the supported RFC 8949 core-deterministic CBOR subset."""
    if _depth > MAX_DEPTH:
        raise AeeWireError("maximum nesting depth exceeded")
    if value is None:
        return b"\xf6"
    if value is False:
        return b"\xf4"
    if value is True:
        return b"\xf5"
    if isinstance(value, int):
        return _head(0, value) if value >= 0 else _head(1, -1 - value)
    if isinstance(value, bytes):
        return _head(2, len(value)) + value
    if isinstance(value, str):
        try:
            raw = value.encode("utf-8", "strict")
        except UnicodeEncodeError as exc:
            raise AeeWireError("text string contains invalid Unicode") from exc
        return _head(3, len(raw)) + raw
    if isinstance(value, (list, tuple)):
        if len(value) > MAX_ITEMS:
            raise AeeWireError("array item limit exceeded")
        return _head(4, len(value)) + b"".join(
            deterministic_cbor_encode(item, _depth=_depth + 1) for item in value
        )
    if isinstance(value, dict):
        if len(value) > MAX_ITEMS:
            raise AeeWireError("map item limit exceeded")
        pairs = []
        for key, item in value.items():
            encoded_key = deterministic_cbor_encode(key, _depth=_depth + 1)
            encoded_value = deterministic_cbor_encode(item, _depth=_depth + 1)
            pairs.append((encoded_key, encoded_value))
        pairs.sort(key=lambda pair: (len(pair[0]), pair[0]))
        for index in range(1, len(pairs)):
            if pairs[index - 1][0] == pairs[index][0]:
                raise AeeWireError("duplicate canonical map key")
        return _head(5, len(pairs)) + b"".join(k + v for k, v in pairs)
    raise AeeWireError(f"unsupported CBOR value type: {type(value).__name__}")


@dataclass
class _Decoder:
    data: bytes
    offset: int = 0
    items: int = 0

    def take(self, count: int) -> bytes:
        if count < 0 or self.offset + count > len(self.data):
            raise AeeWireError("truncated CBOR item")
        value = self.data[self.offset:self.offset + count]
        self.offset += count
        return value

    def argument(self, additional: int) -> int:
        if additional < 24:
            return additional
        sizes = {24: 1, 25: 2, 26: 4, 27: 8}
        size = sizes.get(additional)
        if size is None:
            if additional == 31:
                raise AeeWireError("indefinite-length CBOR is not permitted")
            raise AeeWireError("reserved CBOR additional information")
        value = int.from_bytes(self.take(size), "big")
        minimum = {1: 24, 2: 256, 4: 65536, 8: 4294967296}[size]
        if value < minimum:
            raise AeeWireError("non-minimal CBOR argument encoding")
        return value

    def item(self, depth: int = 0) -> Any:
        if depth > MAX_DEPTH:
            raise AeeWireError("maximum nesting depth exceeded")
        self.items += 1
        if self.items > MAX_ITEMS:
            raise AeeWireError("CBOR item limit exceeded")
        initial = self.take(1)[0]
        major, additional = initial >> 5, initial & 31
        if major == 7:
            if additional == 20:
                return False
            if additional == 21:
                return True
            if additional == 22:
                return None
            raise AeeWireError("floating-point and unsupported simple values are not permitted")
        if major == 6:
            raise AeeWireError("CBOR tags are not supported by this AEE subset")
        arg = self.argument(additional)
        if major == 0:
            return arg
        if major == 1:
            return -1 - arg
        if major == 2:
            if arg > MAX_BYTES:
                raise AeeWireError("byte string size limit exceeded")
            return self.take(arg)
        if major == 3:
            if arg > MAX_BYTES:
                raise AeeWireError("text string size limit exceeded")
            try:
                return self.take(arg).decode("utf-8", "strict")
            except UnicodeDecodeError as exc:
                raise AeeWireError("invalid UTF-8 text string") from exc
        if major == 4:
            if arg > MAX_ITEMS:
                raise AeeWireError("array item limit exceeded")
            return [self.item(depth + 1) for _ in range(arg)]
        if major == 5:
            if arg > MAX_ITEMS:
                raise AeeWireError("map item limit exceeded")
            result = {}
            encoded_keys = set()
            previous_order = None
            for _ in range(arg):
                start = self.offset
                key = self.item(depth + 1)
                encoded_key = self.data[start:self.offset]
                if encoded_key in encoded_keys:
                    raise AeeWireError("duplicate CBOR map key")
                encoded_keys.add(encoded_key)
                order = (len(encoded_key), encoded_key)
                if previous_order is not None and order <= previous_order:
                    raise AeeWireError("CBOR map keys are not in deterministic order")
                previous_order = order
                try:
                    if key in result:
                        raise AeeWireError("duplicate equivalent CBOR map key")
                    value = self.item(depth + 1)
                    result[key] = value
                except TypeError as exc:
                    raise AeeWireError("CBOR map key is not hashable in this profile") from exc
            return result
        raise AeeWireError("unsupported CBOR major type")


def strict_deterministic_cbor_decode(data: bytes) -> Any:
    """Decode one deterministic CBOR item, rejecting trailing bytes."""
    if not isinstance(data, bytes) or not data:
        raise AeeWireError("CBOR input must be non-empty bytes")
    if len(data) > MAX_BYTES:
        raise AeeWireError("CBOR input size limit exceeded")
    decoder = _Decoder(data)
    value = decoder.item()
    if decoder.offset != len(data):
        raise AeeWireError("trailing bytes after CBOR item")
    # Round-trip check guards implementation/representation ambiguities.
    if deterministic_cbor_encode(value) != data:
        raise AeeWireError("CBOR input is not core deterministic encoding")
    return value


def execution_receipt_record_hash(receipt: Mapping[int, Any]) -> bytes:
    """Compute AEE -02 §6.7.1 record-hash from a decoded integer-keyed map.

    This validates the minimal envelope and hashes canonical CBOR itself.
    It does not claim complete CDDL or cryptographic signature validation.
    """
    if not isinstance(receipt, Mapping):
        raise AeeWireError("Execution Receipt must be a map")
    required = {1, 2, 3, 4, 6}
    if not required.issubset(receipt):
        raise AeeWireError("Execution Receipt is missing required envelope keys")
    if receipt[1] != 5 or type(receipt[1]) is not int:
        raise AeeWireError("AEE statement type must be Execution Receipt (5)")
    if type(receipt[2]) is not int or receipt[2] < 0:
        raise AeeWireError("seq must be a non-negative integer")
    if not isinstance(receipt[3], bytes) or len(receipt[3]) != 32:
        raise AeeWireError("prev_hash must be a 32-byte byte string")
    if type(receipt[4]) is not int:
        raise AeeWireError("record_type must be an integer enum")
    if type(receipt[6]) is not int:
        raise AeeWireError("decision must be an integer enum")
    if any(type(key) is not int or key < 0 for key in receipt):
        raise AeeWireError("Execution Receipt keys must be non-negative integers")
    return hashlib.sha256(deterministic_cbor_encode(dict(receipt))).digest()


def verify_execution_receipt_chain(receipts: Iterable[Mapping[int, Any]]) -> tuple[bytes, ...]:
    """Recompute every record hash and verify contiguous seq/prev_hash links."""
    previous = ZERO_HASH
    hashes = []
    for expected_seq, receipt in enumerate(receipts):
        digest = execution_receipt_record_hash(receipt)
        if receipt[2] != expected_seq:
            raise AeeWireError("seq must start at zero and increase by exactly one")
        if receipt[3] != previous:
            raise AeeWireError("prev_hash does not match recomputed preceding record hash")
        hashes.append(digest)
        previous = digest
    if not hashes:
        raise AeeWireError("evidence chain must not be empty")
    return tuple(hashes)


def canonical_json_jcs_bytes(value: Any) -> bytes:
    """Fail-closed placeholder: JSON/JCS is deliberately not claimed here.

    Full RFC 8785 number formatting and I-JSON validation require a dedicated
    implementation and test-vector suite; use CBOR mode in this release.
    """
    raise AeeWireError("JSON/JCS encoding is not implemented in AEE-WIRE-01..03")
