from datetime import date
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
from shapely.geometry import shape
from shapely.validation import explain_validity

STAC_SEARCH_URL = "https://stac.dataspace.copernicus.eu/v1/search"
COLLECTION = "sentinel-2-l2a"

app = FastAPI(
    title="KMH Earth Observation API",
    version="0.1.0",
    description="Myanmar land-change pilot: AOI validation and Sentinel-2 L2A discovery.",
)


class CatalogSearchRequest(BaseModel):
    aoi: dict[str, Any]
    start_date: date
    end_date: date
    max_cloud_cover: float = Field(default=20, ge=0, le=100)
    limit: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def validate_request(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        try:
            geom = shape(self.aoi)
        except Exception as exc:
            raise ValueError("aoi must be a valid GeoJSON geometry") from exc
        if geom.geom_type not in ("Polygon", "MultiPolygon"):
            raise ValueError("aoi must be Polygon or MultiPolygon")
        if geom.is_empty or not geom.is_valid:
            raise ValueError(f"aoi geometry is invalid: {explain_validity(geom)}")
        minx, miny, maxx, maxy = geom.bounds
        if minx < -180 or maxx > 180 or miny < -90 or maxy > 90:
            raise ValueError("aoi coordinates must be WGS84 longitude/latitude")
        return self


@app.get("/health")
async def health():
    return {"status": "ok", "service": "kmh-earth-observation-api", "version": "0.1.0"}


@app.post("/v1/catalog/sentinel-2/search")
async def search_sentinel2(request: CatalogSearchRequest):
    payload = {
        "collections": [COLLECTION],
        "intersects": request.aoi,
        "datetime": (
            f"{request.start_date.isoformat()}T00:00:00Z/"
            f"{request.end_date.isoformat()}T23:59:59Z"
        ),
        "query": {"eo:cloud_cover": {"lte": request.max_cloud_cover}},
        "limit": request.limit,
    }
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(STAC_SEARCH_URL, json=payload)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Copernicus STAC catalogue request failed: {type(exc).__name__}",
        ) from exc

    features = data.get("features", [])
    results = []
    for item in features:
        props = item.get("properties", {})
        results.append({
            "item_id": item.get("id"),
            "collection": item.get("collection"),
            "datetime": props.get("datetime"),
            "cloud_cover": props.get("eo:cloud_cover"),
            "bbox": item.get("bbox"),
            "assets": {
                name: asset.get("href")
                for name, asset in item.get("assets", {}).items()
                if asset.get("href")
            },
        })
    return {
        "collection": COLLECTION,
        "matched_items": len(results),
        "catalogue": "Copernicus Data Space Ecosystem STAC",
        "items": results,
        "next": data.get("links", []),
        "notice": "Discovery metadata only; no imagery has been downloaded or processed.",
    }
