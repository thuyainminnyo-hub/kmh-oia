import hashlib
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from src.image_integrity import verify_png_integrity


def chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))


def ihdr(width=1, height=1, bit_depth=8, color_type=6, interlace=0):
    return struct.pack(">IIBBBBB", width, height, bit_depth, color_type, 0, 0, interlace)


def make_png(pixel=b"\x00\x00\x00\xff"):
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr())
            + chunk(b"IDAT", zlib.compress(b"\x00" + pixel))
            + chunk(b"IEND", b""))


class ImageIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def verify_bytes(self, name, content):
        path = self.root / name
        path.write_bytes(content)
        return verify_png_integrity(str(path), self.root)

    def test_valid_png_passes_and_records_sha256(self):
        raw = make_png()
        result = self.verify_bytes("valid.png", raw)
        self.assertTrue(result.verified, result.reason)
        self.assertTrue(result.decode_verified)
        self.assertEqual(result.detected_format, "PNG")
        self.assertEqual(result.size_bytes, len(raw))
        self.assertEqual(result.sha256, hashlib.sha256(raw).hexdigest())

    def test_corrupt_chunk_crc_fails(self):
        raw = bytearray(make_png())
        raw[29] ^= 0x01
        result = self.verify_bytes("corrupt.png", bytes(raw))
        self.assertFalse(result.verified)
        self.assertIn("CRC mismatch", result.reason)

    def test_truncated_png_fails(self):
        result = self.verify_bytes("truncated.png", make_png()[:-5])
        self.assertFalse(result.verified)

    def test_empty_file_fails(self):
        result = self.verify_bytes("empty.png", b"")
        self.assertFalse(result.verified)

    def test_unsupported_jpeg_fails_closed(self):
        result = self.verify_bytes("image.jpg", b"\xff\xd8\xffnot-a-jpeg")
        self.assertFalse(result.verified)
        self.assertIn("PNG only", result.reason)

    def test_path_outside_root_fails(self):
        with tempfile.TemporaryDirectory() as outside:
            path = Path(outside) / "outside.png"
            path.write_bytes(make_png())
            result = verify_png_integrity(str(path), self.root)
        self.assertFalse(result.verified)
        self.assertIn("escapes", result.reason)

    def test_digest_changes_when_bytes_change(self):
        first = make_png(b"\x00\x00\x00\xff")
        second = make_png(b"\x01\x00\x00\xff")
        a = self.verify_bytes("a.png", first)
        b = self.verify_bytes("b.png", second)
        self.assertTrue(a.verified, a.reason)
        self.assertTrue(b.verified, b.reason)
        self.assertNotEqual(a.sha256, b.sha256)

    def test_rejects_non_consecutive_idat_chunks(self):
        header = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr())
        compressed = zlib.compress(b"\x00\x00\x00\x00\xff")
        raw = header + chunk(b"IDAT", compressed[:2]) + chunk(b"tEXt", b"k\x00v")
        raw += chunk(b"IDAT", compressed[2:]) + chunk(b"IEND", b"")
        result = self.verify_bytes("split-idat.png", raw)
        self.assertFalse(result.verified)
        self.assertIn("consecutive", result.reason)

    def test_rejects_unknown_critical_chunk(self):
        raw = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr())
               + chunk(b"ABCD", b"") + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\xff"))
               + chunk(b"IEND", b""))
        result = self.verify_bytes("critical.png", raw)
        self.assertFalse(result.verified)
        self.assertIn("unknown critical", result.reason)

    def test_rejects_invalid_bit_depth_color_type_combination(self):
        raw = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr(bit_depth=4, color_type=6))
               + chunk(b"IDAT", zlib.compress(b"\x00")) + chunk(b"IEND", b""))
        result = self.verify_bytes("invalid-depth.png", raw)
        self.assertFalse(result.verified)
        self.assertIn("bit depth/color type", result.reason)

    def test_rejects_scanline_output_larger_than_declared_dimensions(self):
        raw = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr())
               + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\xffEXTRA"))
               + chunk(b"IEND", b""))
        result = self.verify_bytes("oversized-decoded.png", raw)
        self.assertFalse(result.verified)
        self.assertIn("expected scanline", result.reason)

    def test_rejects_trailing_bytes_after_iend(self):
        result = self.verify_bytes("trailing.png", make_png() + b"junk")
        self.assertFalse(result.verified)
        self.assertIn("trailing bytes", result.reason)

    def test_rejects_duplicate_iend(self):
        raw = make_png() + chunk(b"IEND", b"")
        result = self.verify_bytes("duplicate-iend.png", raw)
        self.assertFalse(result.verified)
        self.assertIn("trailing bytes", result.reason)

    def test_rejects_invalid_dimensions_before_decode(self):
        raw = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr(width=0))
               + chunk(b"IDAT", zlib.compress(b"")) + chunk(b"IEND", b""))
        result = self.verify_bytes("zero-width.png", raw)
        self.assertFalse(result.verified)
        self.assertIn("dimensions", result.reason)


    def test_valid_indexed_png_with_plte_passes(self):
        header = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr(bit_depth=1, color_type=3))
        palette = chunk(b"PLTE", b"\x00\x00\x00\xff\xff\xff")
        image_data = chunk(b"IDAT", zlib.compress(b"\x00\x00"))
        raw = header + palette + image_data + chunk(b"IEND", b"")
        result = self.verify_bytes("indexed.png", raw)
        self.assertTrue(result.verified, result.reason)

    def test_indexed_png_requires_plte(self):
        raw = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr(bit_depth=1, color_type=3))
               + chunk(b"IDAT", zlib.compress(b"\x00\x00")) + chunk(b"IEND", b""))
        result = self.verify_bytes("indexed-no-plte.png", raw)
        self.assertFalse(result.verified)
        self.assertIn("requires PLTE", result.reason)


    def test_indexed_png_rejects_pixel_index_outside_palette(self):
        header = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr(bit_depth=2, color_type=3))
        palette = chunk(b"PLTE", b"\x00\x00\x00\xff\xff\xff")
        # With 2-bit indices, the top two bits 10 represent palette index 2,
        # while this PLTE contains only entries 0 and 1.
        image_data = chunk(b"IDAT", zlib.compress(b"\x00\x80"))
        raw = header + palette + image_data + chunk(b"IEND", b"")
        result = self.verify_bytes("indexed-bad-palette-index.png", raw)
        self.assertFalse(result.verified)
        self.assertIn("missing PLTE entry", result.reason)

    def test_rejects_chunk_type_with_reserved_bit_set(self):
        header = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr())
        invalid_ancillary = chunk(b"text", b"k\x00v")
        raw = header + invalid_ancillary + chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00\xff"))
        raw += chunk(b"IEND", b"")
        result = self.verify_bytes("reserved-bit.png", raw)
        self.assertFalse(result.verified)
        self.assertIn("reserved bit", result.reason)


    def test_split_idat_payloads_preserve_one_zlib_stream(self):
        header = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr())
        compressed = zlib.compress(b"\x00\x00\x00\x00\xff")
        split = max(1, len(compressed) // 2)
        raw = header + chunk(b"IDAT", compressed[:split]) + chunk(b"IDAT", compressed[split:])
        raw += chunk(b"IEND", b"")
        result = self.verify_bytes("split-idat-valid.png", raw)
        self.assertTrue(result.verified, result.reason)

    def test_indexed_png_ignores_unused_padding_bits_after_last_pixel(self):
        header = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr(width=1, bit_depth=1, color_type=3))
        palette = chunk(b"PLTE", b"\x00\x00\x00\xff\xff\xff")
        # Pixel index is the most-significant bit (0); lower seven padding bits
        # are not pixels and may contain any bit pattern.
        image_data = chunk(b"IDAT", zlib.compress(b"\x00\x7f"))
        raw = header + palette + image_data + chunk(b"IEND", b"")
        result = self.verify_bytes("indexed-padding-bits.png", raw)
        self.assertTrue(result.verified, result.reason)

    def test_rejects_extra_bytes_after_zlib_stream_inside_idat(self):
        header = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr())
        compressed = zlib.compress(b"\x00\x00\x00\x00\xff") + b"\x00EXTRA"
        raw = header + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")
        result = self.verify_bytes("idat-trailing-compressed.png", raw)
        self.assertFalse(result.verified)
        self.assertIn("expected scanline", result.reason)


if __name__ == "__main__":
    unittest.main()
