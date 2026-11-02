#!/usr/bin/env python3
"""Classify imported-symbol references by AST context without running Graphify.

This is independent source evidence only. It models whether an imported name
occurs in a local symbol's AST subtree; it does not execute Graphify or emit a
replacement graph.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    result: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            result[child] = parent
    return result


def _is_within(node: ast.AST, ancestor: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    current = node
    while current in parents:
        current = parents[current]
        if current is ancestor:
            return True
    return node is ancestor


def _annotation_roots(symbol: ast.AST) -> list[ast.AST]:
    roots: list[ast.AST] = []
    if isinstance(symbol, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args = [
            *symbol.args.posonlyargs,
            *symbol.args.args,
            *symbol.args.kwonlyargs,
        ]
        if symbol.args.vararg is not None:
            args.append(symbol.args.vararg)
        if symbol.args.kwarg is not None:
            args.append(symbol.args.kwarg)
        roots.extend(arg.annotation for arg in args if arg.annotation is not None)
        if symbol.returns is not None:
            roots.append(symbol.returns)

    for node in ast.walk(symbol):
        if isinstance(node, ast.AnnAssign):
            roots.append(node.annotation)
    return roots


def analyze_imported_symbol_context(
    source: str,
    *,
    module_name: str,
    imported_name: str,
    symbol_name: str,
    source_file: str = "<memory>",
) -> dict[str, Any]:
    """Report annotation vs executable-body references to one imported symbol."""
    try:
        tree = ast.parse(source, filename=source_file)
    except SyntaxError as exc:
        return {
            "status": "FAIL",
            "errors": [f"Python syntax error at line {exc.lineno}: {exc.msg}"],
            "analysis_mode": "stdlib_ast_context_only_not_graphify_execution",
        }

    import_node = None
    local_name = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module != module_name:
            continue
        for alias in node.names:
            if alias.name == imported_name:
                import_node = node
                local_name = alias.asname or alias.name
                break
        if import_node is not None:
            break

    if import_node is None or local_name is None:
        return {
            "status": "FAIL",
            "errors": [f"{imported_name} is not imported from {module_name}"],
            "analysis_mode": "stdlib_ast_context_only_not_graphify_execution",
        }

    symbol = next(
        (
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == symbol_name
        ),
        None,
    )
    if symbol is None:
        return {
            "status": "FAIL",
            "errors": [f"local symbol {symbol_name} was not found"],
            "analysis_mode": "stdlib_ast_context_only_not_graphify_execution",
        }

    parent_map = _parents(tree)
    annotation_roots = _annotation_roots(symbol)
    sites: list[dict[str, Any]] = []

    for node in ast.walk(symbol):
        if not isinstance(node, ast.Name) or node.id != local_name:
            continue
        if not isinstance(node.ctx, ast.Load):
            continue

        in_annotation = any(
            _is_within(node, annotation_root, parent_map)
            for annotation_root in annotation_roots
        )
        parent = parent_map.get(node)
        if in_annotation:
            context = "TYPE_ANNOTATION"
        elif isinstance(parent, ast.Call) and parent.func is node:
            context = "RUNTIME_CALL"
        else:
            context = "RUNTIME_BODY_REFERENCE"

        sites.append({
            "line": node.lineno,
            "column": node.col_offset,
            "context": context,
        })

    sites.sort(key=lambda item: (item["line"], item["column"], item["context"]))
    counts = {
        context: sum(1 for site in sites if site["context"] == context)
        for context in ("TYPE_ANNOTATION", "RUNTIME_CALL", "RUNTIME_BODY_REFERENCE")
    }
    return {
        "schema_version": "1.0.0",
        "status": "PASS",
        "analysis_mode": "stdlib_ast_context_only_not_graphify_execution",
        "source_file": source_file,
        "import": {
            "module": module_name,
            "imported_name": imported_name,
            "local_name": local_name,
            "line": import_node.lineno,
        },
        "local_symbol": {
            "name": symbol_name,
            "kind": type(symbol).__name__,
            "line": symbol.lineno,
        },
        "reference_sites": sites,
        "reference_counts": counts,
        "resolver_input_assessment": {
            "imported_name_referenced_in_local_symbol": bool(sites),
            "first_reference_line": sites[0]["line"] if sites else None,
            "has_type_annotation_reference": counts["TYPE_ANNOTATION"] > 0,
            "has_runtime_reference": (
                counts["RUNTIME_CALL"] + counts["RUNTIME_BODY_REFERENCE"]
            ) > 0,
            "interpretation": (
                "The imported name appears in this local symbol's AST subtree. "
                "This is source-context evidence only; Graphify has not been executed."
                if sites else
                "The import is present, but this local symbol contains no loaded reference to the imported name."
            ),
        },
        "governance": {
            "owner_disposition": "CONFIRMED_HOLD",
            "edge_confidence": "INFERRED",
            "promotion": "NOT_AUTHORIZED",
            "raw_graph_mutated": False,
            "candidate_graph_mutated": False,
        },
        "errors": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--module", required=True)
    parser.add_argument("--imported-name", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--report-out", required=True, type=Path)
    args = parser.parse_args()

    if not args.source.is_file() or args.source.is_symlink():
        report = {
            "status": "FAIL",
            "errors": ["source file is missing or is a symlink"],
            "analysis_mode": "stdlib_ast_context_only_not_graphify_execution",
        }
    else:
        try:
            source = args.source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            report = {"status": "FAIL", "errors": [str(exc)]}
        else:
            report = analyze_imported_symbol_context(
                source,
                module_name=args.module,
                imported_name=args.imported_name,
                symbol_name=args.symbol,
                source_file=args.source.as_posix(),
            )

    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Imported-symbol AST context: {report['status']}")
    print(f"Analysis mode: {report.get('analysis_mode', 'unknown')}")
    print(f"Reference sites: {len(report.get('reference_sites', []))}")
    print("Graphify extraction performed: NO")
    print("Promotion authorized: NO")
    for error in report.get("errors", []):
        print(f"FAIL: {error}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
