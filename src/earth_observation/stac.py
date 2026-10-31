"""Minimal, auditable Copernicus STAC discovery client."""
from __future__ import annotations
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

STAC_SEARCH_URL = "https://stac.dataspace.copernicus.eu/v1/search"
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
                raise AOIValidationError("Each position must contain numeric longitude and latitude")
            lon, lat = position[0], position[1]
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                raise AOIValidationError("Coordinates must be within WGS84 bounds")
    outer = coordinates[0]
    if len({(p[0], p[1]) for p in outer[:-1]}) < 3:
        raise AOIValidationError("Outer ring must contain at least three distinct vertices")
    return geometry

def search_sentinel2(geometry: dict[str, Any], datetime_range: str, *,
                     cloud_cover_max: float = 30.0, limit: int = 100,
                     timeout: int = 30) -> list[dict[str, Any]]:
    """Search Sentinel-2 L2A metadata; does not download or process imagery."""
    validate_aoi(geometry)
    if not datetime_range or "/" not in datetime_range:
        raise ValueError("datetime_range must be an ISO-8601 interval")
    if not 0 <= cloud_cover_max <= 100:
        raise ValueError("cloud_cover_max must be between 0 and 100")
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    payload = {"collections": [COLLECTION], "intersects": geometry,
               "datetime": datetime_range, "limit": limit}
    request = Request(STAC_SEARCH_URL, data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json",
                               "Accept": "application/geo+json"}, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            document = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise STACRequestError(f"Copernicus STAC search failed: {exc}") from exc
    features = document.get("features")
    if not isinstance(features, list):
        raise STACRequestError("STAC response did not contain a features array")
    return [feature for feature in features
            if isinstance(feature, dict)
            and isinstance(feature.get("properties"), dict)
            and isinstance(feature["properties"].get("eo:cloud_cover"), (int, float))
            and feature["properties"]["eo:cloud_cover"] <= cloud_cover_max]
