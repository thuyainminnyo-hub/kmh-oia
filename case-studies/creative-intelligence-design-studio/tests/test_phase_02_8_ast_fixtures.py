import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "phase_02_8" / "src"


def parse(relative):
    return ast.parse((FIXTURE / relative).read_text(encoding="utf-8"))


def top_level(tree, name, node_type):
    return next(
        node for node in tree.body
        if isinstance(node, node_type) and getattr(node, "name", None) == name
    )


class Phase028AstFixtureTests(unittest.TestCase):
    def test_ctx01_parameter_annotation_is_ast_parameter(self):
        tree = parse("pkg_alpha/service.py")
        fn = top_level(tree, "parameter_only", ast.FunctionDef)
        self.assertIsInstance(fn.args.args[0].annotation, ast.Name)
        self.assertEqual(fn.args.args[0].annotation.id, "AlphaWidget")

    def test_ctx02_return_annotation_is_independent_ast_field(self):
        tree = parse("pkg_alpha/service.py")
        fn = top_level(tree, "return_only", ast.FunctionDef)
        self.assertIsInstance(fn.returns, ast.Name)
        self.assertEqual(fn.returns.id, "AlphaWidget")

    def test_ctx03_same_line_parameter_and_return_are_two_ast_roots(self):
        tree = parse("pkg_alpha/service.py")
        fn = top_level(tree, "same_line", ast.FunctionDef)
        parameter = fn.args.args[0].annotation
        returned = fn.returns
        self.assertEqual(parameter.id, "AlphaWidget")
        self.assertEqual(returned.id, "AlphaWidget")
        self.assertEqual(parameter.lineno, returned.lineno)

    def test_ctx04_annotated_assignment_has_variable_annotation(self):
        tree = parse("pkg_alpha/service.py")
        assignment = next(node for node in tree.body if isinstance(node, ast.AnnAssign))
        self.assertIsInstance(assignment.annotation, ast.Name)
        self.assertEqual(assignment.annotation.id, "AlphaWidget")

    def test_ctx05_multiple_inheritance_has_each_base(self):
        tree = parse("pkg_alpha/service.py")
        child = top_level(tree, "AlphaChild", ast.ClassDef)
        self.assertEqual([base.id for base in child.bases], ["AlphaBase", "AlphaMixin"])

    def test_ctx06_alias_import_preserves_local_and_original_names(self):
        tree = parse("pkg_alpha/service.py")
        imported = next(node for node in tree.body if isinstance(node, ast.ImportFrom))
        alias = next(item for item in imported.names if item.name == "Widget")
        self.assertEqual(alias.name, "Widget")
        self.assertEqual(alias.asname, "AlphaWidget")

    def test_ctx07_same_named_types_are_in_different_modules(self):
        alpha = parse("pkg_alpha/types.py")
        beta = parse("pkg_beta/types.py")
        alpha_widget = top_level(alpha, "Widget", ast.ClassDef)
        beta_widget = top_level(beta, "Widget", ast.ClassDef)
        self.assertEqual(alpha_widget.name, beta_widget.name)
        self.assertNotEqual("pkg_alpha.types", "pkg_beta.types")

    def test_ctx08_nested_function_has_its_own_scope(self):
        tree = parse("pkg_alpha/service.py")
        outer = top_level(tree, "outer", ast.FunctionDef)
        inner = next(node for node in ast.walk(outer) if isinstance(node, ast.FunctionDef) and node.name == "inner")
        self.assertIsInstance(inner.args.args[0].annotation, ast.Name)
        self.assertEqual(inner.args.args[0].annotation.id, "AlphaWidget")
        self.assertTrue(any(isinstance(node, ast.Call) for node in ast.walk(inner)))

    def test_ctx09_string_forward_reference_is_explicit_constant(self):
        tree = parse("pkg_alpha/service.py")
        fn = top_level(tree, "forward_reference", ast.FunctionDef)
        self.assertIsInstance(fn.args.args[0].annotation, ast.Constant)
        self.assertEqual(fn.args.args[0].annotation.value, "AlphaWidget")
        self.assertIsInstance(fn.returns, ast.Constant)

    def test_ctx10_generic_annotation_contains_nested_symbol(self):
        tree = parse("pkg_alpha/service.py")
        fn = top_level(tree, "generic_reference", ast.FunctionDef)
        names = [node.id for node in ast.walk(fn.args.args[0].annotation) if isinstance(node, ast.Name)]
        return_names = [node.id for node in ast.walk(fn.returns) if isinstance(node, ast.Name)]
        self.assertIn("AlphaWidget", names)
        self.assertIn("AlphaWidget", return_names)

    def test_ctx11_star_import_is_not_a_named_binding(self):
        tree = parse("star_import.py")
        imported = next(node for node in tree.body if isinstance(node, ast.ImportFrom))
        self.assertEqual([item.name for item in imported.names], ["*"])

    def test_ctx12_duplicate_declarations_are_ambiguous(self):
        tree = parse("ambiguous.py")
        repeated = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Repeated"]
        self.assertEqual(len(repeated), 2)
        self.assertNotEqual(repeated[0].lineno, repeated[1].lineno)


if __name__ == "__main__":
    unittest.main()
