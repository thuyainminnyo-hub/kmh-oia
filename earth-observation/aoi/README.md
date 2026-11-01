# Taunggyi District AOI

The pilot AOI is the complete Taunggyi District boundary, not a point or an
approximate rectangle.

## Source
MIMU-attributed ArcGIS Feature Service:
- Service layer: `Districts - Admin 2` (FeatureServer layer 3)
- Administrative level: Admin 2
- Boundary standard: MIMU PCode v9.4
- Output CRS: WGS 84 longitude/latitude (EPSG:4326 / CRS84)

Source metadata identifies the layer as Myanmar District polygons based on
MIMU PCode v9.4 and states that the data is reference material, not a warranty
of legal boundary accuracy. Attribute source/attribution must be retained.

## Fetch
```bash
python aoi/fetch_taunggyi_district.py
```

The fetcher requires exactly one feature whose `ADM2_EN` is Taunggyi,
valid polygon geometry, and writes `taunggyi_district.geojson`. The
downloaded geometry is a runtime artifact and is intentionally not fabricated
or hand-drawn in this repository.

## Satellite discovery
After fetching the AOI:
```bash
python scripts/select_sentinel2_scenes.py
```

The discovery script queries Sentinel-2 L2A for two matching dry-season windows.
It ranks scene candidates by catalogue cloud cover only. Scene selection is not
final until AOI-level cloud/shadow masking, valid-pixel coverage, co-registration
and seasonal comparability pass QA.
