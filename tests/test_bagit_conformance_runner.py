import tempfile
import unittest
from pathlib import Path

from scripts.run_bagit_conformance import validate_bag_declaration


class BagDeclarationTests(unittest.TestCase):
    def test_valid_bag_declaration(self):
        with tempfile.TemporaryDirectory() as tmp:
            bag = Path(tmp)
            (bag / "bagit.txt").write_text(
                "BagIt-Version: 1.0\nTag-File-Character-Encoding: UTF-8\n",
                encoding="utf-8",
            )
            self.assertEqual(validate_bag_declaration(bag), (True, ""))

    def test_rejects_whitespace_before_colon(self):
        with tempfile.TemporaryDirectory() as tmp:
            bag = Path(tmp)
            (bag / "bagit.txt").write_text(
                "BagIt-Version : 1.0\nTag-File-Character-Encoding : UTF-8\n",
                encoding="utf-8",
            )
            valid, reason = validate_bag_declaration(bag)
            self.assertFalse(valid)
            self.assertIn("BagIt-Version", reason)

    def test_rejects_wrong_line_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            bag = Path(tmp)
            (bag / "bagit.txt").write_text("BagIt-Version: 1.0\n", encoding="utf-8")
            self.assertFalse(validate_bag_declaration(bag)[0])

    def test_accepts_crlf_line_endings(self):
        with tempfile.TemporaryDirectory() as tmp:
            bag = Path(tmp)
            (bag / "bagit.txt").write_bytes(
                b"BagIt-Version: 1.0\\r\\nTag-File-Character-Encoding: UTF-8\\r\\n"
            )
            self.assertEqual(validate_bag_declaration(bag), (True, ""))

    def test_rejects_utf8_bom(self):
        with tempfile.TemporaryDirectory() as tmp:
            bag = Path(tmp)
            (bag / "bagit.txt").write_bytes(
                b"\\xef\\xbb\\xbfBagIt-Version: 1.0\\nTag-File-Character-Encoding: UTF-8\\n"
            )
            valid, reason = validate_bag_declaration(bag)
            self.assertFalse(valid)
            self.assertIn("BOM", reason)

if __name__ == "__main__":
    unittest.main()
