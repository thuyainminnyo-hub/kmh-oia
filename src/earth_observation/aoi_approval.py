"""Fail-closed authorization checks for campus area-of-interest records."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from src.earth_observation.stac import AOIValidationError, validate_aoi


class AOIApprovalError(ValueError):
    """Raised when a campus AOI lacks verifiable approval metadata."""


def geometry_sha256(geometry: dict[str, Any]) -> str:
    """Hash normalized JSON representation; not a topological geometry hash."""
    validate_aoi(geometry)
    canonical = json.dumps(
        geometry, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def require_approved_aoi(record: dict[str, Any]) -> dict[str, Any]:
    """Return an AOI record only when its explicit approval fields are complete.

    This validates record structure and hash consistency. It does not authenticate
    the approver or independently establish land ownership; those require a human
    review of the cited authorization evidence.
    """
    if not isinstance(record, dict):
        raise AOIApprovalError("AOI approval record must be an object")
    if record.get("status") != "APPROVED":
        raise AOIApprovalError("Campus AOI must have status APPROVED")
    if record.get("crs") != "EPSG:4326":
        raise AOIApprovalError("Campus AOI CRS must be EPSG:4326")
    if not isinstance(record.get("aoi_id"), str) or not record["aoi_id"].strip():
        raise AOIApprovalError("aoi_id is required")
    if not isinstance(record.get("approved_by"), str) or not record["approved_by"].strip():
        raise AOIApprovalError("approved_by is required")
    evidence_uri = record.get("approval_evidence_uri")
    if not isinstance(evidence_uri, str) or not evidence_uri.startswith("https://"):
        raise AOIApprovalError("HTTPS approval evidence URI is required")
    approved_at = record.get("approved_at")
    if not isinstance(approved_at, str):
        raise AOIApprovalError("approved_at must be an ISO-8601 timestamp")
    try:
        datetime.fromisoformat(approved_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AOIApprovalError("approved_at must be a valid ISO-8601 timestamp") from exc
    geometry = record.get("geometry")
    try:
        actual_hash = geometry_sha256(geometry)
    except (AOIValidationError, TypeError) as exc:
        raise AOIApprovalError(f"Invalid campus geometry: {exc}") from exc
    if record.get("geometry_sha256") != actual_hash:
        raise AOIApprovalError("Approved geometry hash does not match supplied geometry")
    return record


def search_approved_campus_aoi(
    record: dict[str, Any],
    datetime_range: str,
    **search_options: Any,
) -> list[dict[str, Any]]:
    """Run campus discovery only after the AOI approval record passes validation."""
    approved = require_approved_aoi(record)
    from src.earth_observation.stac import search_sentinel2

    return search_sentinel2(
        approved["geometry"], datetime_range, **search_options
    )
