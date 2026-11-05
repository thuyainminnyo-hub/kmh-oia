import tempfile
import unittest
from pathlib import Path

from src.output_verification import verify_output_file


class OutputVerificationTests(unittest.TestCase):
    def test_accepts_non_empty_file_under_allowed_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "assets" / "image.png"
            output.parent.mkdir()
            output.write_bytes(b"synthetic image bytes")

            result = verify_output_file("assets/image.png", root)

            self.assertTrue(result.verified)
            self.assertEqual(result.size_bytes, len(b"synthetic image bytes"))
            self.assertEqual(Path(result.resolved_path), output.resolve())

    def test_rejects_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = verify_output_file("missing.png", tmp)
            self.assertFalse(result.verified)
            self.assertIn("does not exist", result.reason)

    def test_rejects_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "empty.png").write_bytes(b"")
            result = verify_output_file("empty.png", tmp)
            self.assertFalse(result.verified)
            self.assertIn("empty", result.reason)

    def test_rejects_path_outside_allowed_root(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            outside_file = Path(outside, "secret.bin")
            outside_file.write_bytes(b"not allowed")
            result = verify_output_file(str(outside_file), tmp)
            self.assertFalse(result.verified)
            self.assertIn("escapes", result.reason)

    def test_rejects_directory_as_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "folder").mkdir()
            result = verify_output_file("folder", tmp)
            self.assertFalse(result.verified)
            self.assertIn("regular file", result.reason)

    def test_rejects_blank_path(self):
        result = verify_output_file(" ", ".")
        self.assertFalse(result.verified)
        self.assertIn("non-empty", result.reason)


if __name__ == "__main__":
    unittest.main()
