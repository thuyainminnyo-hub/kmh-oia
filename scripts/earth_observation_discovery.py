"""Live Copernicus discovery from an approved, fingerprinted GeoJSON Feature."""
import argparse
import json
from pathlib import Path

from src.earth_observation.approval import validate_approved_feature
from src.earth_observation.stac import search_sentinel2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("geojson", type=Path)
    parser.add_argument("--datetime", required=True, dest="datetime_range")
    parser.add_argument("--cloud-cover-max", type=float, default=30.0)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    document = json.loads(args.geojson.read_text(encoding="utf-8"))
    geometry = validate_approved_feature(document)
    items = search_sentinel2(geometry, args.datetime_range,
        cloud_cover_max=args.cloud_cover_max, limit=args.limit)
    print(json.dumps({
        "source": "Copernicus Data Space Ecosystem STAC",
        "collection": "sentinel-2-l2a",
        "aoi_file": str(args.geojson),
        "aoi_approval_status": document["properties"]["approval_status"],
        "aoi_geometry_sha256": document["properties"]["geometry_sha256"],
        "datetime": args.datetime_range,
        "cloud_cover_max": args.cloud_cover_max,
        "catalogue_items_after_filter": len(items),
        "items": [{
            "id": item.get("id"),
            "datetime": item.get("properties", {}).get("datetime"),
            "cloud_cover": item.get("properties", {}).get("eo:cloud_cover"),
            "assets": sorted(item.get("assets", {}).keys()),
        } for item in items],
        "interpretation": "Catalogue discovery only; imagery has not been downloaded or scientifically validated."
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
