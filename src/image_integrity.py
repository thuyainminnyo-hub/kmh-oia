"""Fail-closed PNG integrity verification for local production outputs.

V1 intentionally supports non-interlaced PNG only. The parser validates chunk
ordering, CRCs, IHDR constraints, bounded decompression and scanline filters.
It records a digest of the verified bytes; it does not establish visual
quality, policy compliance, or image authenticity.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct
import zlib

from src.output_verification import verify_output_file

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_MAX_DIMENSION = 100_000
_MAX_DECOMPRESSED_BYTES = 256 * 1024 * 1024
_MAX_FILE_BYTES = 512 * 1024 * 1024


@dataclass(frozen=True)
class ImageIntegrityResult:
    verified: bool
    resolved_path: str | None = None
    size_bytes: int = 0
    sha256: str | None = None
    detected_format: str | None = None
    decode_verified: bool = False
    reason: str | None = None


def verify_png_integrity(output_path: str, allowed_root: str | Path) -> ImageIntegrityResult:
    """Verify a contained non-empty PNG and hash the exact bytes read."""
    basic = verify_output_file(output_path, allowed_root)
    if not basic.verified or basic.resolved_path is None:
        return ImageIntegrityResult(False, size_bytes=basic.size_bytes, reason=basic.reason)
    if basic.size_bytes > _MAX_FILE_BYTES:
        return ImageIntegrityResult(False, basic.resolved_path, basic.size_bytes,
                                    reason="PNG file exceeds safety limit")
    try:
        path = Path(basic.resolved_path)
        raw = path.read_bytes()
        if len(raw) != basic.size_bytes:
            return ImageIntegrityResult(False, resolved_path=str(path), size_bytes=len(raw),
                                        reason="file changed while being read")
        _validate_png(raw)
        return ImageIntegrityResult(
            True, str(path), len(raw), hashlib.sha256(raw).hexdigest(),
            "PNG", True, None,
        )
    except (OSError, ValueError, struct.error, zlib.error) as exc:
        return ImageIntegrityResult(
            False, basic.resolved_path, basic.size_bytes,
            detected_format="PNG" if raw_signature_is_png(output_path) else None,
            decode_verified=False, reason=f"PNG integrity verification failed: {exc}",
        )


def raw_signature_is_png(path: str) -> bool:
    """Best-effort format hint for failed results; never used to accept a file."""
    try:
        with Path(path).open("rb") as stream:
            return stream.read(8) == _PNG_SIGNATURE
    except OSError:
        return False


def _validate_png(raw: bytes) -> tuple[int, int]:
    if not raw.startswith(_PNG_SIGNATURE):
        raise ValueError("unsupported image format; v1 accepts PNG only")

    offset = len(_PNG_SIGNATURE)
    width = height = bit_depth = color_type = None
    seen_ihdr = seen_idat = seen_iend = False
    idat_closed = False
    compressed = bytearray()

    while offset < len(raw):
        if offset + 12 > len(raw):
            raise ValueError("truncated chunk header")
        length = struct.unpack_from(">I", raw, offset)[0]
        chunk_type = raw[offset + 4:offset + 8]
        data_start = offset + 8
        data_end = data_start + length
        end = data_end + 4
        if end > len(raw):
            raise ValueError("truncated chunk data")
        if any(not (65 <= byte <= 90 or 97 <= byte <= 122) for byte in chunk_type):
            raise ValueError("invalid PNG chunk type")
        data = raw[data_start:data_end]
        expected_crc = struct.unpack_from(">I", raw, data_end)[0]
        if zlib.crc32(chunk_type + data) & 0xffffffff != expected_crc:
            raise ValueError("chunk CRC mismatch")

        if not seen_ihdr:
            if chunk_type != b"IHDR" or length != 13:
                raise ValueError("IHDR must be the first chunk")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", data)
            if width == 0 or height == 0 or width > _MAX_DIMENSION or height > _MAX_DIMENSION:
                raise ValueError("invalid image dimensions")
            valid_depths = {
                0: {1, 2, 4, 8, 16},
                2: {8, 16},
                3: {1, 2, 4, 8},
                4: {8, 16},
                6: {8, 16},
            }
            if color_type not in valid_depths or bit_depth not in valid_depths[color_type]:
                raise ValueError("invalid PNG bit depth/color type")
            if compression != 0 or filtering != 0 or interlace != 0:
                raise ValueError("unsupported PNG compression, filter, or interlace method")
            channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
            row_bytes = (width * channels * bit_depth + 7) // 8
            expected_decoded = height * (row_bytes + 1)
            if expected_decoded > _MAX_DECOMPRESSED_BYTES:
                raise ValueError("decoded image exceeds safety limit")
            seen_ihdr = True
        elif chunk_type == b"IHDR":
            raise ValueError("duplicate IHDR")
        elif chunk_type == b"IDAT":
            if idat_closed:
                raise ValueError("IDAT chunks must be consecutive")
            seen_idat = True
            if len(compressed) + length > _MAX_FILE_BYTES:
                raise ValueError("compressed image data exceeds safety limit")
            compressed.extend(data)
        elif chunk_type == b"IEND":
            if length != 0 or not seen_idat:
                raise ValueError("invalid IEND or missing IDAT")
            if seen_iend:
                raise ValueError("duplicate IEND")
            seen_iend = True
            offset = end
            break
        else:
            if seen_idat:
                idat_closed = True
            # The first chunk-type byte's lowercase bit marks ancillary chunks.
            if not (chunk_type[0] & 0x20):
                raise ValueError(f"unknown critical chunk {chunk_type!r}")
        offset = end

    if not seen_ihdr or not seen_idat or not seen_iend:
        raise ValueError("missing required PNG chunk")
    if offset != len(raw):
        raise ValueError("trailing bytes after IEND")

    # Check the declared decompressed size before decompressing or collecting
    # decoded rows. max_length prevents oversized output from being materialized.
    decoder = zlib.decompressobj()
    decoded = decoder.decompress(bytes(compressed), expected_decoded + 1)
    if len(decoded) != expected_decoded or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError("IDAT data does not decode to expected scanline length")
    if any(decoded[row * (row_bytes + 1)] > 4 for row in range(height)):
        raise ValueError("invalid PNG scanline filter")
    return width, height
