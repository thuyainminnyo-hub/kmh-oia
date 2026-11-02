import unittest

from scripts.analyze_inferred_edge_context import analyze_imported_symbol_context


class InferredEdgeContextTests(unittest.TestCase):
    def analyze(self, body: str, *, import_line: str = "from contract_guard import DesignToken"):
        source = f"{import_line}\n\n{body}"
        return analyze_imported_symbol_context(
            source,
            module_name="contract_guard",
            imported_name="DesignToken",
            symbol_name="select_outfit",
            source_file="synthetic_fixture.py",
        )

    def test_annotation_only_is_classified_as_type_annotation(self):
        result = self.analyze(
            "def select_outfit(token: DesignToken):\n"
            "    return None\n"
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["reference_counts"]["TYPE_ANNOTATION"], 1)
        self.assertFalse(result["resolver_input_assessment"]["has_runtime_reference"])
        self.assertEqual(result["resolver_input_assessment"]["first_reference_line"], 3)

    def test_runtime_constructor_is_classified_as_runtime_call(self):
        result = self.analyze(
            "def select_outfit():\n"
            "    return DesignToken()\n"
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["reference_counts"]["RUNTIME_CALL"], 1)
        self.assertFalse(result["resolver_input_assessment"]["has_type_annotation_reference"])
        self.assertEqual(result["resolver_input_assessment"]["first_reference_line"], 4)

    def test_mixed_annotation_and_runtime_call_are_separated(self):
        result = self.analyze(
            "def select_outfit(token: DesignToken):\n"
            "    return DesignToken(token.token_name)\n"
        )
        self.assertEqual(result["reference_counts"]["TYPE_ANNOTATION"], 1)
        self.assertEqual(result["reference_counts"]["RUNTIME_CALL"], 1)
        self.assertTrue(result["resolver_input_assessment"]["has_runtime_reference"])

    def test_unused_import_does_not_create_a_symbol_reference(self):
        result = self.analyze(
            "def select_outfit():\n"
            "    return None\n"
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["reference_sites"], [])
        self.assertFalse(result["resolver_input_assessment"]["imported_name_referenced_in_local_symbol"])

    def test_typed_parameter_field_read_is_not_a_second_design_token_name_reference(self):
        result = self.analyze(
            "def select_outfit(token: DesignToken):\n"
            "    return token.token_name\n"
        )
        self.assertEqual(result["reference_counts"]["TYPE_ANNOTATION"], 1)
        self.assertEqual(result["reference_counts"]["RUNTIME_BODY_REFERENCE"], 0)
        self.assertFalse(result["resolver_input_assessment"]["has_runtime_reference"])

    def test_import_alias_is_resolved_to_local_name(self):
        result = self.analyze(
            "def select_outfit(token: Token):\n"
            "    return None\n",
            import_line="from contract_guard import DesignToken as Token",
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["import"]["local_name"], "Token")
        self.assertEqual(result["reference_counts"]["TYPE_ANNOTATION"], 1)

    def test_return_annotation_is_classified_as_type_annotation(self):
        result = self.analyze(
            "def select_outfit() -> DesignToken:\n"
            "    return None\n"
        )
        self.assertEqual(result["reference_counts"]["TYPE_ANNOTATION"], 1)
        self.assertFalse(result["resolver_input_assessment"]["has_runtime_reference"])

    def test_bad_module_is_rejected(self):
        result = analyze_imported_symbol_context(
            "from other_module import DesignToken\ndef select_outfit(x): return x\n",
            module_name="contract_guard",
            imported_name="DesignToken",
            symbol_name="select_outfit",
        )
        self.assertEqual(result["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
