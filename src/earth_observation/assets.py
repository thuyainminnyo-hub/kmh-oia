"""Validate required Sentinel-2 L2A assets before any acquisition attempt."""
from __future__ import annotations

from typing import Any


class AssetValidationError(ValueError):
    """Raised when a catalogue item lacks required, verifiable raster assets."""


REQUIRED_L2A_ASSETS = {
    "B04_10m": 10,
    "B08_10m": 10,
    "SCL_20m": 20,
}


def validate_l2a_assets(item: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return required asset metadata after checking roles, resolution and integrity hints.

    This function validates catalogue metadata only. It does not fetch asset bytes
    or verify the remote checksum against downloaded content.
    """
    assets = item.get("assets")
    if not isinstance(assets, dict):
        raise AssetValidationError("STAC item has no assets object")
    selected: dict[str, dict[str, Any]] = {}
    for key, expected_gsd in REQUIRED_L2A_ASSETS.items():
        asset = assets.get(key)
        if not isinstance(asset, dict):
            raise AssetValidationError(f"Required asset missing: {key}")
        if asset.get("type") != "image/jp2":
            raise AssetValidationError(f"{key} must be an image/jp2 asset")
        if "data" not in asset.get("roles", []):
            raise AssetValidationError(f"{key} must have the data role")
        if asset.get("gsd") != expected_gsd:
            raise AssetValidationError(
                f"{key} expected {expected_gsd}m GSD, got {asset.get('gsd')}"
            )
        if not isinstance(asset.get("file:size"), int) or asset["file:size"] <= 0:
            raise AssetValidationError(f"{key} must declare a positive file:size")
        checksum = asset.get("file:checksum")
        if not isinstance(checksum, str) or not checksum:
            raise AssetValidationError(f"{key} must declare file:checksum")
        href = asset.get("href")
        alternates = asset.get("alternate", {})
        https_href = alternates.get("https", {}).get("href") if isinstance(alternates, dict) else None
        if not (isinstance(href, str) and href.startswith("s3://")) and not (
            isinstance(https_href, str) and https_href.startswith("https://")
        ):
            raise AssetValidationError(f"{key} has no supported S3 or HTTPS asset location")
        selected[key] = asset
    return selected
