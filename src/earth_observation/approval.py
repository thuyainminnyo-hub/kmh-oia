"""Approval gate for campus AOIs before any live catalogue query."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .stac import AOIValidationError, validate_aoi


class AOIApprovalError(ValueError):
    """Raised when a campus AOI lacks verifiable approval metadata."""


def geometry_sha256(geometry: dict[str, Any]) -> str:
    """Hash canonical geometry JSON; approval metadata is excluded."""
    canonical = json.dumps(
        geometry, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def validate_approved_feature(feature: dict[str, Any]) -> dict[str, Any]:
    """Require an approved GeoJSON Feature and verify its geometry fingerprint.

    This validates the supplied approval record's structure and integrity only.
    It does not independently authenticate the named approver or evidence URI.
    """
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        raise AOIApprovalError("AOI input must be an approved GeoJSON Feature")
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        raise AOIApprovalError("AOI approval properties are required")
    required = {
        "approval_status": "APPROVED",
        "approver_name": None,
        "approver_role": None,
        "approved_at": None,
        "approval_evidence_ref": None,
        "boundary_source": None,
        "boundary_version": None,
        "geometry_sha256": None,
    }
    if properties.get("approval_status") != "APPROVED":
        raise AOIApprovalError("Campus AOI is not APPROVED; live search is blocked")
    for key, expected in required.items():
        if key == "approval_status":
            continue
        value = properties.get(key)
        if not isinstance(value, str) or not value.strip():
            raise AOIApprovalError(f"Missing required approval field: {key}")
    geometry = feature.get("geometry")
    try:
        validate_aoi(geometry)
    except (AOIValidationError, TypeError) as exc:
        raise AOIApprovalError(f"Invalid AOI geometry: {exc}") from exc
    actual = geometry_sha256(geometry)
    if properties["geometry_sha256"].lower() != actual:
        raise AOIApprovalError("AOI geometry SHA-256 does not match approval record")
    return geometry
