"""Fail-closed PNG integrity verification for local production outputs.

V1 intentionally supports non-interlaced PNG only. The parser validates chunk
ordering, CRCs, IHDR constraints, bounded decompression and scanline filters.
It records a digest of the verified bytes; it does not establish visual
quality, policy compliance, or image authenticity.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat
import struct
import zlib

from src.output_verification import verify_output_file

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# Keep peak parser memory bounded for this local pilot. The file cap limits
# the raw input plus retained IDAT data; the decoded cap bounds zlib output.
_MAX_DIMENSION = 100_000
_MAX_DECOMPRESSED_BYTES = 64 * 1024 * 1024
_MAX_FILE_BYTES = 32 * 1024 * 1024
_MAX_PNG_CHUNKS = 10_000


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
        root = Path(allowed_root).resolve()
        raw = _read_contained_file_no_follow(path, root)
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
            decode_verified=False, reason=f"PNG integrity verification failed: {exc}",
        )


def _read_contained_file_no_follow(path: Path, root: Path) -> bytes:
    """Read a regular file under root without following any path symlink.

    Directory descriptors anchor each path traversal step, so a parent directory
    or final filename swapped to a symlink between validation and read fails closed.
    """
    relative = path.relative_to(root)
    parts = relative.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("output path is not a safe relative path under the allowed root")

    directory_flag = getattr(os, "O_DIRECTORY", 0)
    no_follow_flag = getattr(os, "O_NOFOLLOW", 0)
    if not directory_flag or not no_follow_flag or not hasattr(os, "supports_dir_fd") or os.open not in os.supports_dir_fd:
        raise OSError("platform lacks safe directory-relative, no-follow file opening")

    root_fd = os.open(root, os.O_RDONLY | directory_flag | no_follow_flag)
    parent_fd = root_fd
    opened_fds = []
    try:
        for component in parts[:-1]:
            parent_fd = os.open(component, os.O_RDONLY | directory_flag | no_follow_flag, dir_fd=parent_fd)
            opened_fds.append(parent_fd)
        file_fd = os.open(parts[-1], os.O_RDONLY | no_follow_flag, dir_fd=parent_fd)
        try:
            before = os.fstat(file_fd)
            if not stat.S_ISREG(before.st_mode):
                raise OSError("output path is not a regular file")
            if before.st_size <= 0:
                raise ValueError("output file is empty")
            if before.st_size > _MAX_FILE_BYTES:
                raise ValueError("PNG file exceeds safety limit")
            chunks = []
            remaining = _MAX_FILE_BYTES + 1
            while remaining > 0:
                block = os.read(file_fd, min(1024 * 1024, remaining))
                if not block:
                    break
                chunks.append(block)
                remaining -= len(block)
            raw = b"".join(chunks)
            after = os.fstat(file_fd)
            identity_before = (before.st_dev, before.st_ino, before.st_size,
                               before.st_mtime_ns, before.st_ctime_ns)
            identity_after = (after.st_dev, after.st_ino, after.st_size,
                              after.st_mtime_ns, after.st_ctime_ns)
            if identity_before != identity_after or len(raw) != before.st_size:
                raise ValueError("file changed while being read")
            if len(raw) > _MAX_FILE_BYTES:
                raise ValueError("PNG file exceeds safety limit")
            return raw
        finally:
            os.close(file_fd)
    finally:
        for fd in reversed(opened_fds):
            os.close(fd)
        os.close(root_fd)


def _validate_png(raw: bytes) -> tuple[int, int]:
    if not raw.startswith(_PNG_SIGNATURE):
        raise ValueError("unsupported image format; v1 accepts PNG only")

    offset = len(_PNG_SIGNATURE)
    width = height = bit_depth = color_type = None
    seen_ihdr = seen_plte = seen_idat = seen_iend = False
    idat_closed = False
    compressed = bytearray()
    palette_entries = None

    chunk_count = 0
    while offset < len(raw):
        chunk_count += 1
        if chunk_count > _MAX_PNG_CHUNKS:
            raise ValueError("PNG exceeds maximum chunk count")
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
        # PNG reserves the third chunk-type byte as uppercase. Reject rather
        # than interpreting a type with its reserved bit set.
        if chunk_type[2] & 0x20:
            raise ValueError("PNG chunk type reserved bit must be zero")
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
        elif chunk_type == b"PLTE":
            if seen_plte or seen_idat:
                raise ValueError("PLTE must appear at most once before IDAT")
            if color_type in (0, 4):
                raise ValueError("PLTE is not permitted for grayscale color types")
            if length == 0 or length % 3 != 0 or length > 768:
                raise ValueError("invalid PLTE length")
            if color_type == 3 and length // 3 > (1 << bit_depth):
                raise ValueError("PLTE has more entries than indexed bit depth permits")
            palette_entries = length // 3
            seen_plte = True
        elif chunk_type == b"IDAT":
            if idat_closed:
                raise ValueError("IDAT chunks must be consecutive")
            if color_type == 3 and not seen_plte:
                raise ValueError("indexed-color PNG requires PLTE before IDAT")
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
    decoded = decoder.decompress(compressed, expected_decoded + 1)
    if len(decoded) != expected_decoded or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError("IDAT data does not decode to expected scanline length")
    if any(decoded[row * (row_bytes + 1)] > 4 for row in range(height)):
        raise ValueError("invalid PNG scanline filter")

    # For indexed-color PNGs, reconstruct filtered rows before reading packed
    # pixel indices. The bit-depth range alone is not sufficient: each index
    # must also refer to an entry actually present in PLTE.
    if color_type == 3:
        if palette_entries is None:
            raise ValueError("indexed-color PNG requires PLTE before IDAT")
        bytes_per_pixel = max(1, (bit_depth + 7) // 8)
        previous_row = bytes(row_bytes)
        for row_index in range(height):
            start = row_index * (row_bytes + 1)
            filter_type = decoded[start]
            filtered_row = decoded[start + 1:start + 1 + row_bytes]
            row = _unfilter_scanline(filter_type, filtered_row, previous_row, bytes_per_pixel)
            for pixel_x in range(width):
                bit_offset = pixel_x * bit_depth
                shift = 8 - bit_depth - (bit_offset % 8)
                palette_index = (row[bit_offset // 8] >> shift) & ((1 << bit_depth) - 1)
                if palette_index >= palette_entries:
                    raise ValueError("indexed-color pixel references missing PLTE entry")
            previous_row = row

    return width, height


def _unfilter_scanline(filter_type: int, filtered: bytes, previous: bytes,
                       bytes_per_pixel: int) -> bytes:
    """Reconstruct one PNG scanline from its filter representation."""
    reconstructed = bytearray(len(filtered))
    for i, value in enumerate(filtered):
        left = reconstructed[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
        up = previous[i] if previous else 0
        upper_left = previous[i - bytes_per_pixel] if previous and i >= bytes_per_pixel else 0

        if filter_type == 0:  # None
            predictor = 0
        elif filter_type == 1:  # Sub
            predictor = left
        elif filter_type == 2:  # Up
            predictor = up
        elif filter_type == 3:  # Average
            predictor = (left + up) // 2
        elif filter_type == 4:  # Paeth
            estimate = left + up - upper_left
            distance_left = abs(estimate - left)
            distance_up = abs(estimate - up)
            distance_upper_left = abs(estimate - upper_left)
            if distance_left <= distance_up and distance_left <= distance_upper_left:
                predictor = left
            elif distance_up <= distance_upper_left:
                predictor = up
            else:
                predictor = upper_left
        else:
            raise ValueError("invalid PNG scanline filter")
        reconstructed[i] = (value + predictor) & 0xff
    return bytes(reconstructed)
