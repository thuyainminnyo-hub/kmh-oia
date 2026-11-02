#!/usr/bin/env python3
"""Build an EXTRACTED-only Graphify promotion candidate from a hash-pinned review manifest."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

EDGE_IDENTITY_FIELDS = (
    "source",
    "target",
    "relation",
    "confidence",
    "source_file",
    "source_location",
)


class ReviewError(ValueError):
    """Raised when the review manifest does not safely match the source graph."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def edge_identity(edge: dict[str, Any]) -> dict[str, Any]:
    identity = {key: edge.get(key) for key in EDGE_IDENTITY_FIELDS}
    missing = [key for key, value in identity.items() if value in (None, "")]
    if missing:
        raise ReviewError(f"edge identity is incomplete; missing: {', '.join(missing)}")
    return identity


def edge_fingerprint(edge: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(edge_identity(edge))).hexdigest()


def build_candidate(raw_graph_bytes: bytes, raw_graph: dict[str, Any], manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    actual_graph_sha = hashlib.sha256(raw_graph_bytes).hexdigest()
    source_artifact = manifest.get("source_artifact", {})
    if actual_graph_sha != source_artifact.get("graph_sha256"):
        raise ReviewError("raw graph SHA-256 does not match the hash-pinned review manifest")

    raw_edges = raw_graph.get("edges")
    if not isinstance(raw_edges, list):
        raise ReviewError("raw Graphify graph must contain an edges array")
    decisions = manifest.get("edge_decisions")
    if not isinstance(decisions, list):
        raise ReviewError("review manifest must contain edge_decisions")

    decisions_by_fingerprint: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        if not isinstance(decision, dict):
            raise ReviewError("each edge decision must be an object")
        fingerprint = decision.get("edge_fingerprint")
        if not isinstance(fingerprint, str) or len(fingerprint) != 64:
            raise ReviewError("each edge decision requires a SHA-256 edge_fingerprint")
        if fingerprint in decisions_by_fingerprint:
            raise ReviewError(f"duplicate review decision for edge fingerprint {fingerprint}")
        decisions_by_fingerprint[fingerprint] = decision

    raw_edge_by_fingerprint: dict[str, dict[str, Any]] = {}
    for edge in raw_edges:
        if not isinstance(edge, dict):
            raise ReviewError("raw graph contains a non-object edge")
        fingerprint = edge_fingerprint(edge)
        if fingerprint in raw_edge_by_fingerprint:
            raise ReviewError("raw graph contains duplicate edge identities; refusing ambiguous review")
        raw_edge_by_fingerprint[fingerprint] = edge

    for fingerprint, decision in decisions_by_fingerprint.items():
        if fingerprint not in raw_edge_by_fingerprint:
            raise ReviewError(f"review decision does not match any edge in the pinned raw graph: {fingerprint}")
        if decision.get("edge_identity") != edge_identity(raw_edge_by_fingerprint[fingerprint]):
            raise ReviewError("review decision edge_identity does not match its fingerprint")

    extracted_edges: list[dict[str, Any]] = []
    excluded_edges: list[dict[str, Any]] = []
    seen_edge_fingerprints: set[str] = set()
    confidence_counts: Counter[str] = Counter()

    for edge in raw_edges:
        confidence = edge.get("confidence")
        confidence_counts[str(confidence)] += 1
        fingerprint = edge_fingerprint(edge)
        if fingerprint in seen_edge_fingerprints:
            raise ReviewError("edge fingerprint collision or duplicate edge detected")
        seen_edge_fingerprints.add(fingerprint)

        if confidence == "EXTRACTED":
            if not edge.get("source_file") or not edge.get("source_location"):
                raise ReviewError("EXTRACTED edge is missing source_file or source_location")
            extracted_edges.append(copy.deepcopy(edge))
            continue

        decision = decisions_by_fingerprint.get(fingerprint)
        if decision is None:
            raise ReviewError(
                f"non-EXTRACTED edge {edge.get('relation')} at "
                f"{edge.get('source_file')}:{edge.get('source_location')} has no explicit review decision"
            )
        if decision.get("disposition") not in {"HOLD_NOT_PROMOTED", "REJECT_FROM_CANDIDATE"}:
            raise ReviewError("non-EXTRACTED edges cannot be promoted by this EXTRACTED-only workflow")
        if decision.get("owner_confirmation") != "PENDING":
            raise ReviewError("owner confirmation must remain pending for this review candidate")
        excluded_edges.append({
            "edge_identity": edge_identity(edge),
            "edge_fingerprint": fingerprint,
            "disposition": decision["disposition"],
            "reason_code": decision.get("reason_code"),
            "rationale": decision.get("rationale"),
            "superseded_by_edge": decision.get("superseded_by_edge"),
            "owner_confirmation": decision["owner_confirmation"],
        })

    if set(decisions_by_fingerprint) - seen_edge_fingerprints:
        raise ReviewError("one or more review decisions were not consumed")

    candidate_graph = copy.deepcopy(raw_graph)
    candidate_graph["edges"] = extracted_edges
    candidate_bytes = json.dumps(candidate_graph, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    candidate_sha = hashlib.sha256(candidate_bytes).hexdigest()
    report = {
        "schema_version": "1.0.0",
        "promotion_status": "CANDIDATE_ONLY_OWNER_CONFIRMATION_PENDING",
        "raw_graph_sha256": actual_graph_sha,
        "candidate_graph_sha256": candidate_sha,
        "source_artifact": source_artifact,
        "raw_graph_counts": {
            "nodes": len(raw_graph.get("nodes", [])),
            "edges": len(raw_edges),
            "confidence": dict(confidence_counts),
        },
        "candidate_graph_counts": {
            "nodes": len(candidate_graph.get("nodes", [])),
            "edges": len(extracted_edges),
            "confidence": dict(Counter(edge["confidence"] for edge in extracted_edges)),
        },
        "excluded_edges": excluded_edges,
        "unanchored_external_nodes_retained_as_external_references": [
            {"id": node.get("id"), "label": node.get("label"), "external": node.get("external", False)}
            for node in candidate_graph.get("nodes", [])
            if node.get("external") is True or node.get("source_file") in (None, "")
        ],
        "owner_confirmation": "PENDING",
        "production_promotion": "NOT_AUTHORIZED",
        "raw_graph_mutated": False,
    }
    return candidate_graph, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True, type=Path)
    parser.add_argument("--decisions", required=True, type=Path)
    parser.add_argument("--candidate-out", required=True, type=Path)
    parser.add_argument("--report-out", required=True, type=Path)
    args = parser.parse_args()
    raw_bytes = args.graph.read_bytes()
    raw_graph = json.loads(raw_bytes)
    manifest = json.loads(args.decisions.read_text(encoding="utf-8"))
    candidate, report = build_candidate(raw_bytes, raw_graph, manifest)
    args.candidate_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.candidate_out.write_text(json.dumps(candidate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Graph review: {report['promotion_status']}")
    print(f"Edges: {report['raw_graph_counts']['edges']} raw -> {report['candidate_graph_counts']['edges']} extracted-only candidate")
    print(f"Excluded for review: {len(report['excluded_edges'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
