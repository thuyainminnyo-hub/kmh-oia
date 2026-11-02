import tempfile
import unittest
from pathlib import Path

from scripts.validate_inferred_edge_evidence import inspect_held_edge


class HeldEdgeSourceEvidenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "outfit_flow.py").write_text(
            "from contract_guard import DesignToken, is_approved_token\n\n\n\n\n"
            "def select_outfit(token: DesignToken) -> dict[str, str]:\n"
            "    if not is_approved_token(token):\n"
            "        raise ValueError('not approved')\n"
            "    return {'token': token.token_name, 'status': 'selected'}\n",
            encoding="utf-8",
        )
        (self.root / "src" / "contract_guard.py").write_text(
            "from dataclasses import dataclass\n\n"
            "@dataclass(frozen=True)\n"
            "class DesignToken:\n"
            "    token_name: str\n"
            "    approved: bool\n\n"
            "def is_approved_token(token: DesignToken) -> bool:\n"
            "    return bool(token.token_name.strip()) and token.approved\n",
            encoding="utf-8",
        )

    def test_import_annotation_and_runtime_use_are_corroborated(self):
        result = inspect_held_edge(self.root)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["decision"]["owner_disposition"], "CONFIRMED_HOLD")
        self.assertEqual(result["decision"]["promotion"], "NOT_AUTHORIZED")
        self.assertTrue(result["evidence"]["type_annotation"]["matches_graph_edge_source_location"])
        self.assertTrue(result["evidence"]["runtime_parameter_field_access"])

    def test_wrong_import_source_fails(self):
        path = self.root / "src" / "outfit_flow.py"
        path.write_text(path.read_text().replace("from contract_guard import DesignToken, is_approved_token",
                                                "from elsewhere import DesignToken, is_approved_token"))
        self.assertEqual(inspect_held_edge(self.root)["status"], "FAIL")

    def test_wrong_type_annotation_fails(self):
        path = self.root / "src" / "outfit_flow.py"
        path.write_text(path.read_text().replace("token: DesignToken", "token: object"))
        self.assertEqual(inspect_held_edge(self.root)["status"], "FAIL")

    def test_missing_target_class_fails(self):
        path = self.root / "src" / "contract_guard.py"
        path.write_text("class OtherToken:\n    pass\n", encoding="utf-8")
        self.assertEqual(inspect_held_edge(self.root)["status"], "FAIL")

    def test_missing_field_access_fails(self):
        path = self.root / "src" / "outfit_flow.py"
        path.write_text(path.read_text().replace("token.token_name", "str(token)"))
        self.assertEqual(inspect_held_edge(self.root)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
