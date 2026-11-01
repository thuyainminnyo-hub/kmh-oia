"""Fetch Taunggyi District boundary from the MIMU-attributed ArcGIS service.

The script deliberately downloads the authoritative feature geometry at runtime;
it does not substitute a hand-drawn bounding box for an administrative boundary.
"""
import json
from pathlib import Path

import requests
from shapely.geometry import shape, mapping
from shapely.validation import explain_validity

SERVICE = (
    "https://services7.arcgis.com/75E2CRDA8iMPOf2z/"
    "ArcGIS/rest/services/Myanmar_admin_boundaries/FeatureServer/3/query"
)
OUT = Path(__file__).with_name("taunggyi_district.geojson")


def main():
    params = {
        "where": "UPPER(ADM2_EN) = 'TAUNGGYI'",
        "outFields": "ADM2_EN,ADM2_MY,ADM2_PCODE,ADM1_EN,ADM1_PCODE,ADM0_EN",
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
    }
    response = requests.get(SERVICE, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()
    features = data.get("features", [])
    if len(features) != 1:
        raise RuntimeError(
            f"Expected exactly one Taunggyi District feature; received {len(features)}. "
            "Inspect the source attributes before proceeding."
        )
    feature = features[0]
    props = feature.get("properties", feature.get("attributes", {}))
    geom = shape(feature["geometry"])
    if geom.is_empty or not geom.is_valid:
        raise RuntimeError(f"Invalid source geometry: {explain_validity(geom)}")
    if geom.geom_type not in ("Polygon", "MultiPolygon"):
        raise RuntimeError(f"Unexpected geometry type: {geom.geom_type}")
    if props.get("ADM2_EN", "").strip().lower() != "taunggyi":
        raise RuntimeError(f"Unexpected district returned: {props.get('ADM2_EN')!r}")
    output = {
        "type": "FeatureCollection",
        "name": "Taunggyi District, Shan State, Myanmar",
        "source": SERVICE,
        "attribution": "MIMU / GAD administrative boundary data; see source terms",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": [{
            "type": "Feature",
            "id": feature.get("id", props.get("ADM2_PCODE")),
            "properties": props,
            "geometry": mapping(geom),
        }],
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(OUT),
        "district": props.get("ADM2_EN"),
        "state_region": props.get("ADM1_EN"),
        "pcode": props.get("ADM2_PCODE"),
        "geometry_type": geom.geom_type,
        "bounds_wgs84": geom.bounds,
        "area_km2_epsg6933": round(
            __import__("pyproj").Transformer.from_crs(
                "EPSG:4326", "EPSG:6933", always_xy=True
            ).transform_bounds(*geom.bounds)[2], 3
        ) if False else None,
        "valid": geom.is_valid,
        "feature_count": 1,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
