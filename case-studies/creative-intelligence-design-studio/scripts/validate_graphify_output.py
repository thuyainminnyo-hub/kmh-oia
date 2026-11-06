#!/usr/bin/env python3
"""Verify Graphify output against the two-file synthetic source snapshot."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

ALLOWED_SOURCE_FILES = {"src/contract_guard.py", "src/outfit_flow.py"}
REQUIRED_SYMBOLS = {
    "src/contract_guard.py": {"designtoken", "is_approved_token"},
    "src/outfit_flow.py": {"select_outfit"},
}
VALID_CONFIDENCES = {"EXTRACTED", "INFERRED", "AMBIGUOUS"}


def normalize_source_path(value: Any, scan_root: Path) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().replace("\\", "/")
    candidate = Path(raw)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(scan_root.resolve()).as_posix()
        except (OSError, ValueError):
            return None
    pure = PurePosixPath(raw)
    if pure.is_absolute() or ".." in pure.parts:
        return None
    normalized = pure.as_posix()
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def parse_line(value: Any) -> int | None:
    match = re.fullmatch(r"L([1-9][0-9]*)", str(value or ""))
    return int(match.group(1)) if match else None


def normalize_label(value: Any) -> str:
    label = str(value or "").strip()
    if label.endswith("()"):
        label = label[:-2]
    return label.rsplit(".", 1)[-1].casefold()


def validate_graph(graph: dict[str, Any], scan_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    notes: list[str] = []
    scan_root = Path(scan_root).resolve()
    source_lines: dict[str, list[str]] = {}

    for relative in sorted(ALLOWED_SOURCE_FILES):
        source_path = scan_root / relative
        if not source_path.is_file() or source_path.is_symlink():
            errors.append(f"approved source file missing or unsafe: {relative}")
            continue
        source_lines[relative] = source_path.read_text(encoding="utf-8").splitlines()

    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        return {"status": "FAIL", "errors": ["graph.json must contain a nodes list"], "notes": notes}

    edges = graph.get("edges") if "edges" in graph else graph.get("links")
    if not isinstance(edges, list):
        errors.append("graph.json must contain an edges or links list")
        edges = []

    nodes_by_id: dict[str, dict[str, Any]] = {}
    node_source: dict[str, str | None] = {}
    labels_by_source: dict[str, set[str]] = {key: set() for key in ALLOWED_SOURCE_FILES}
    source_node_counts: Counter[str] = Counter()
    unanchored_nodes = 0

    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"node {index} is not an object")
            continue
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"node {index} has a missing or non-string id")
            continue
        if node_id in nodes_by_id:
            errors.append(f"duplicate node id: {node_id}")
            continue
        nodes_by_id[node_id] = node
        relative = normalize_source_path(node.get("source_file"), scan_root)
        node_source[node_id] = relative
        if relative is None:
            if node.get("source_file") not in ("", None):
                errors.append(f"node {node_id} has an external or invalid source_file")
            else:
                unanchored_nodes += 1
            continue
        if relative not in ALLOWED_SOURCE_FILES:
            errors.append(f"node {node_id} references non-allowlisted source: {relative}")
            continue
        source_node_counts[relative] += 1
        labels_by_source[relative].add(normalize_label(node.get("label")))
        line = parse_line(node.get("source_location"))
        if line is None:
            errors.append(f"node {node_id} lacks a valid L<number> source_location")
        elif line > len(source_lines.get(relative, [])):
            errors.append(f"node {node_id} source line {line} exceeds {relative} length")

    missing_symbols = []
    for relative, required in REQUIRED_SYMBOLS.items():
        missing = sorted(required - labels_by_source.get(relative, set()))
        missing_symbols.extend(f"{relative}:{symbol}" for symbol in missing)
    if missing_symbols:
        errors.append("required fixture symbols missing from graph: " + ", ".join(missing_symbols))

    confidence_counts: Counter[str] = Counter()
    edge_source_counts: Counter[str] = Counter()
    cross_file_edges: list[dict[str, Any]] = []
    review_edges: list[dict[str, Any]] = []
    extracted_edges_with_source = 0

    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"edge {index} is not an object")
            continue
        source_id, target_id = edge.get("source"), edge.get("target")
        if not isinstance(source_id, str) or source_id not in nodes_by_id:
            errors.append(f"edge {index} source id does not resolve: {source_id!r}")
        if not isinstance(target_id, str) or (
            target_id not in nodes_by_id and edge.get("relation") not in {"imports", "imports_from", "re_exports"}
        ):
            errors.append(f"edge {index} target id does not resolve: {target_id!r}")

        confidence = str(edge.get("confidence") or "")
        if confidence not in VALID_CONFIDENCES:
            errors.append(f"edge {index} has invalid confidence: {confidence!r}")
            continue
        confidence_counts[confidence] += 1

        edge_source = normalize_source_path(edge.get("source_file"), scan_root)
        if edge_source not in ALLOWED_SOURCE_FILES:
            errors.append(f"edge {index} source_file is outside the two-file snapshot")
            continue
        line = parse_line(edge.get("source_location"))
        if line is None:
            errors.append(f"edge {index} lacks a valid L<number> source_location")
        elif line > len(source_lines.get(edge_source, [])):
            errors.append(f"edge {index} line {line} exceeds {edge_source} length")
        edge_source_counts[edge_source] += 1
        if confidence == "EXTRACTED":
            extracted_edges_with_source += 1

        target_source = node_source.get(target_id) if isinstance(target_id, str) else None
        if target_source is None and edge.get("target_file"):
            target_source = normalize_source_path(edge.get("target_file"), scan_root)
        if target_source is not None and target_source not in ALLOWED_SOURCE_FILES:
            errors.append(f"edge {index} target_file escapes the approved snapshot")
        if target_source in ALLOWED_SOURCE_FILES and target_source != edge_source:
            cross_file_edges.append({
                "source": edge_source,
                "target": target_source,
                "relation": edge.get("relation"),
                "confidence": confidence,
                "source_location": edge.get("source_location"),
                "source_label": nodes_by_id.get(source_id, {}).get("label"),
                "target_label": nodes_by_id.get(target_id, {}).get("label") if isinstance(target_id, str) else None,
            })
        if confidence in {"INFERRED", "AMBIGUOUS"}:
            review_edges.append({
                "source": edge_source,
                "relation": edge.get("relation"),
                "confidence": confidence,
                "source_location": edge.get("source_location"),
                "source_label": nodes_by_id.get(source_id, {}).get("label"),
                "target_label": nodes_by_id.get(target_id, {}).get("label") if isinstance(target_id, str) else None,
            })

    represented_sources = sorted(path for path, count in source_node_counts.items() if count)
    if set(represented_sources) != ALLOWED_SOURCE_FILES:
        errors.append("graph must contain source-backed nodes from both approved Python fixtures")
    if not cross_file_edges:
        errors.append("no cross-file edge connects the two approved synthetic fixtures")
    if not extracted_edges_with_source:
        errors.append("graph contains no EXTRACTED edge with a source file and line")
    if unanchored_nodes:
        notes.append(f"{unanchored_nodes} unanchored/external-reference node(s) were not used as source evidence")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "notes": notes,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "source_node_counts": dict(source_node_counts),
        "source_edge_counts": dict(edge_source_counts),
        "represented_source_files": represented_sources,
        "confidence_counts": dict(confidence_counts),
        "cross_file_edges": cross_file_edges,
        "inferred_or_ambiguous_edges_for_review": review_edges,
        "unanchored_node_count": unanchored_nodes,
        "expected_symbols": {source: sorted(symbols) for source, symbols in REQUIRED_SYMBOLS.items()},
    }


def render_report(summary: dict[str, Any], tool_version: str, source_commit: str) -> str:
    lines = [
        "# KMH Graphify Disposable Pilot - Traceability QA",
        "",
        f"Result: {summary.get('status', 'FAIL')}",
        f"Graphify version: {tool_version}",
        f"Graphify source commit: {source_commit}",
        "",
        "## Graph summary",
        "",
        f"- Nodes: {summary.get('node_count', 0)}",
        f"- Edges: {summary.get('edge_count', 0)}",
        f"- Source-backed files: {', '.join(summary.get('represented_source_files', []))}",
        f"- Confidence counts: {json.dumps(summary.get('confidence_counts', {}), sort_keys=True)}",
        f"- Cross-file edges: {len(summary.get('cross_file_edges', []))}",
        f"- Unanchored nodes: {summary.get('unanchored_node_count', 0)}",
        "",
        "## Cross-file evidence",
        "",
    ]
    for edge in summary.get("cross_file_edges", []):
        lines.append(
            f"- {edge.get('source')}:{edge.get('source_location')} "
            f"-[{edge.get('relation')} / {edge.get('confidence')}]-> "
            f"{edge.get('target')} ({edge.get('source_label')} -> {edge.get('target_label')})"
        )
    if not summary.get("cross_file_edges"):
        lines.append("- None")
    lines.extend(["", "## INFERRED / AMBIGUOUS edges requiring human review", ""])
    for edge in summary.get("inferred_or_ambiguous_edges_for_review", []):
        lines.append(
            f"- {edge.get('confidence')}: {edge.get('source')}:{edge.get('source_location')} "
            f"[{edge.get('relation')}] {edge.get('source_label')} -> {edge.get('target_label')}"
        )
    if not summary.get("inferred_or_ambiguous_edges_for_review"):
        lines.append("- None emitted by this code-only run.")
    lines.extend(["", "## Errors", ""])
    lines.extend([f"- {item}" for item in summary.get("errors", [])] or ["- None"])
    lines.extend(["", "## Notes", ""])
    lines.extend([f"- {item}" for item in summary.get("notes", [])] or ["- None"])
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- EXTRACTED edges are source-backed structural evidence and must retain a file/line reference.",
        "- INFERRED edges remain hypotheses; they are not automatically promoted to facts.",
        "- AMBIGUOUS edges remain review items.",
        "- This report covers only two synthetic Python fixtures, not KMH OIA production code or MLCW assets.",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True, type=Path)
    parser.add_argument("--scan-root", required=True, type=Path)
    parser.add_argument("--summary-out", required=True, type=Path)
    parser.add_argument("--report-out", required=True, type=Path)
    parser.add_argument("--tool-version", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args(argv)
    try:
        graph = json.loads(args.graph.read_text(encoding="utf-8"))
        summary = validate_graph(graph, args.scan_root)
    except (OSError, json.JSONDecodeError) as exc:
        summary = {"status": "FAIL", "errors": [f"cannot read graph.json: {exc}"]}
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.summary_out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    args.report_out.write_text(render_report(summary, args.tool_version, args.source_commit), encoding="utf-8")
    print(f"Graphify traceability QA: {summary.get('status')}")
    print(f"Nodes: {summary.get('node_count', 0)}; edges: {summary.get('edge_count', 0)}")
    print(f"Cross-file edges: {len(summary.get('cross_file_edges', []))}")
    for error in summary.get("errors", []):
        print(f"FAIL: {error}")
    return 0 if summary.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
