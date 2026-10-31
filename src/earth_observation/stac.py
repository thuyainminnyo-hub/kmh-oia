"""Minimal, auditable Copernicus STAC discovery client with safe pagination."""
from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

STAC_SEARCH_URL = "https://stac.opensearch.dataspace.copernicus.eu/v1/search"
STAC_HOST = "stac.opensearch.dataspace.copernicus.eu"
STAC_PATH = "/v1/search"
COLLECTION = "sentinel-2-l2a"


class AOIValidationError(ValueError):
    """Raised when an AOI is not a valid WGS84 GeoJSON Polygon."""


class STACRequestError(RuntimeError):
    """Raised when the STAC API cannot provide a valid response."""


def validate_aoi(geometry: dict[str, Any]) -> dict[str, Any]:
    """Structural validation only; this does not approve a campus boundary."""
    if not isinstance(geometry, dict) or geometry.get("type") != "Polygon":
        raise AOIValidationError("AOI geometry must be a GeoJSON Polygon")
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        raise AOIValidationError("Polygon coordinates are required")
    for ring in coordinates:
        if not isinstance(ring, list) or len(ring) < 4:
            raise AOIValidationError("Each linear ring needs at least four positions")
        if ring[0] != ring[-1]:
            raise AOIValidationError("Linear rings must be closed")
        for position in ring:
            if (not isinstance(position, (list, tuple)) or len(position) < 2
                    or not isinstance(position[0], (int, float))
                    or not isinstance(position[1], (int, float))):
                raise AOIValidationError(
                    "Each position must contain numeric longitude and latitude"
                )
            lon, lat = position[0], position[1]
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise AOIValidationError("Coordinates must be within WGS84 bounds")
    outer = coordinates[0]
    if len({(p[0], p[1]) for p in outer[:-1]}) < 3:
        raise AOIValidationError("Outer ring must contain at least three distinct vertices")
    return geometry


def _decode_feature_page(response: Any) -> tuple[list[dict[str, Any]], str | None]:
    try:
        document = json.loads(response.read().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise STACRequestError("Copernicus STAC returned invalid JSON") from exc
    features = document.get("features")
    if not isinstance(features, list):
        raise STACRequestError("STAC response did not contain a features array")
    next_link = next(
        (link for link in document.get("links", [])
         if isinstance(link, dict) and link.get("rel") == "next"),
        None,
    )
    return features, next_link.get("href") if next_link else None


def _validate_next_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != STAC_HOST or parsed.path != STAC_PATH:
        raise STACRequestError("STAC pagination link points outside the approved search endpoint")
    return url


def search_sentinel2(
    geometry: dict[str, Any],
    datetime_range: str,
    *,
    cloud_cover_max: float = 30.0,
    limit: int = 100,
    timeout: int = 30,
    max_pages: int = 100,
) -> list[dict[str, Any]]:
    """Search Sentinel-2 L2A metadata across all safe STAC pages.

    This discovers catalogue metadata only; it does not download or process imagery.
    Cloud-cover filtering is client-side and items without a numeric cloud-cover
    property are excluded from the filtered result.
    """
    validate_aoi(geometry)
    if not datetime_range or "/" not in datetime_range:
        raise ValueError("datetime_range must be an ISO-8601 interval")
    if not 0 <= cloud_cover_max <= 100:
        raise ValueError("cloud_cover_max must be between 0 and 100")
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    if not 1 <= max_pages <= 1000:
        raise ValueError("max_pages must be between 1 and 1000")

    payload = {
        "collections": [COLLECTION],
        "intersects": geometry,
        "datetime": datetime_range,
        "limit": limit,
    }
    request = Request(
        STAC_SEARCH_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/geo+json"},
        method="POST",
    )
    items: list[dict[str, Any]] = []
    seen_next_urls: set[str] = set()

    try:
        with urlopen(request, timeout=timeout) as response:
            features, next_url = _decode_feature_page(response)
        pages = 1
        while True:
            items.extend(
                feature for feature in features if isinstance(feature, dict)
            )
            if not next_url:
                break
            if pages >= max_pages:
                raise STACRequestError(f"STAC pagination exceeded max_pages={max_pages}")
            safe_url = _validate_next_url(next_url)
            if safe_url in seen_next_urls:
                raise STACRequestError("STAC pagination returned a repeated next link")
            seen_next_urls.add(safe_url)
            next_request = Request(
                safe_url, headers={"Accept": "application/geo+json"}, method="GET"
            )
            with urlopen(next_request, timeout=timeout) as response:
                features, next_url = _decode_feature_page(response)
            pages += 1
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise STACRequestError(f"Copernicus STAC search failed: {exc}") from exc

    return [
        item for item in items
        if isinstance(item.get("properties"), dict)
        and isinstance(item["properties"].get("eo:cloud_cover"), (int, float))
        and item["properties"]["eo:cloud_cover"] <= cloud_cover_max
    ]
