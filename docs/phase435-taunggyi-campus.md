# Phase 435 — KMH Earth Observation Pilot V1 (Chindwin Taunggyi)

## Confirmed public facts
- Institution: Chindwin Technological University, Taunggyi Campus.
- Published address: No.57/16, Myat Yadanar Street, Yae Aye Kwin Quarter, Taunggyi, Shan State, Myanmar.
- Official page reports 7,888 sq ft and four floors. This is a building/floor-area description, not a verified land parcel or campus AOI polygon.
- The official page's embedded Google Maps iframe resolves to a map center near 97.0485373 E, 20.7998693 N. This is a map center, not a surveyed campus boundary.

## AOI status: HOLD
Do not use the map center, address geocoder point, building footprint, or published floor area as a campus polygon. Obtain a boundary GeoJSON from an authorized campus representative or trace a proposed boundary against authoritative imagery and obtain written campus approval. Record approver, approval time, CRS (WGS84 / EPSG:4326), source, and version.

Suggested evidence fields: aoi_id, institution, campus_name, geometry, crs, boundary_source, boundary_version, approved_by, approved_at, approval_evidence_uri, created_at, sha256.

## Copernicus catalogue
- STAC API: https://stac.dataspace.copernicus.eu/v1/
- Collection: sentinel-2-l2a
- Search endpoint: POST https://stac.dataspace.copernicus.eu/v1/search
- Collection metadata identifies B04 (Red) and B08 (NIR) at 10 m GSD; SWIR bands are 20 m.
- The public collection metadata endpoint was opened successfully during research. No campus-intersection item search has been executed because no approved AOI is available.

## Run discovery after approval
    python scripts/earth_observation_discovery.py approved-campus-aoi.geojson --datetime 2026-01-01T00:00:00Z/2026-10-31T23:59:59Z --cloud-cover-max 30

The script reports STAC catalogue items and asset keys. It does not download imagery, calculate NDVI, or prove vegetation condition.

## Implementation scope in this branch
- Structural GeoJSON Polygon validation (closed rings and WGS84 coordinate ranges).
- Copernicus STAC POST search.
- Client-side cloud-cover filtering.
- Unit tests with mocked HTTP responses.
- CLI for real catalogue discovery once an approved AOI is supplied.

## Not implemented / not verified
- Official campus boundary acquisition or approval.
- Real STAC item discovery for this campus.
- Satellite asset download and authentication.
- Raster decoding, cloud masking, NDVI calculation.
- Scientific review, OIA evidence-adapter integration.
- Production deployment.

## Decision gates
1. AOI approval: campus representative supplies or approves polygon.
2. Catalogue discovery: live STAC response archived with timestamp and request parameters.
3. Asset acquisition: B04/B08 assets downloaded and checksummed.
4. Processing: reflectance scaling, QA/SCL masking, raster alignment, NDVI.
5. Scientific QA: uncertainty, no-data, spatial representativeness and temporal comparability reviewed.
6. OIA admission: provenance and review evidence accepted by KMH OIA.
