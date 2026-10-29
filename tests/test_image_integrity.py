import hashlib
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from src.image_integrity import verify_png_integrity


def make_png(pixel=b"\x00\x00\x00\xff"):
    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff))
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
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


if __name__ == "__main__":
    unittest.main()
