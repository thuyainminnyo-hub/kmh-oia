"""Discover candidate Sentinel-2 L2A scenes for two comparable seasonal windows.

Run fetch_taunggyi_district.py first. This script selects candidates by AOI
intersection and cloud cover; it does not download imagery or claim change results.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pystac_client
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
AOI_FILE = ROOT / "aoi" / "taunggyi_district.geojson"
OUTPUT = ROOT / "data" / "taunggyi_scene_candidates.json"
CATALOG_URL = "https://stac.dataspace.copernicus.eu/v1"
COLLECTION = "sentinel-2-l2a"
MAX_CLOUD = 30

# Comparable dry-season windows; adjust only with an explicit pilot decision.
WINDOWS = {
    "baseline": ("2024-11-01T00:00:00Z", "2025-02-28T23:59:59Z"),
    "comparison": ("2025-11-01T00:00:00Z", "2026-02-28T23:59:59Z"),
}


def main():
    if not AOI_FILE.exists():
        raise FileNotFoundError(
            f"{AOI_FILE} missing. Run: python aoi/fetch_taunggyi_district.py"
        )
    fc = json.loads(AOI_FILE.read_text(encoding="utf-8"))
    if len(fc.get("features", [])) != 1:
        raise RuntimeError("AOI file must contain exactly one district feature.")
    geom = fc["features"][0]["geometry"]
    shape(geom)  # validate that the geometry can be parsed
    catalog = pystac_client.Client.open(CATALOG_URL)
    results = {}
    for label, (start, end) in WINDOWS.items():
        search = catalog.search(
            collections=[COLLECTION],
            intersects=geom,
            datetime=f"{start}/{end}",
            query={"eo:cloud_cover": {"lte": MAX_CLOUD}},
            max_items=500,
        )
        items = list(search.items())
        items.sort(key=lambda item: (
            item.properties.get("eo:cloud_cover", 100),
            item.datetime or datetime.max.replace(tzinfo=timezone.utc),
        ))
        results[label] = [{
            "item_id": item.id,
            "collection": item.collection_id,
            "datetime": item.datetime.isoformat() if item.datetime else None,
            "cloud_cover_percent": item.properties.get("eo:cloud_cover"),
            "platform": item.properties.get("platform"),
            "processing_baseline": item.properties.get("s2:processing_baseline"),
            "assets": {
                key: asset.href for key, asset in item.assets.items()
            },
        } for item in items[:20]]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "catalog": CATALOG_URL,
        "collection": COLLECTION,
        "aoi": "Taunggyi District, Shan State, Myanmar",
        "max_cloud_cover_percent": MAX_CLOUD,
        "windows": WINDOWS,
        "selection_policy": (
            "Candidate ranking only: lowest reported scene cloud cover first. "
            "Final selection requires AOI cloud-mask coverage, valid-pixel and "
            "seasonal comparability QA."
        ),
        "candidates": results,
        "searched_at_utc": datetime.now(timezone.utc).isoformat(),
    }, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "baseline_candidates": len(results["baseline"]),
        "comparison_candidates": len(results["comparison"]),
        "catalogue_search_completed": True,
        "imagery_downloaded": False,
    }, indent=2))


if __name__ == "__main__":
    main()
