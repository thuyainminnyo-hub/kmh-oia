# Phase 435 — KMH Earth Observation Pilot V1 (Chindwin Taunggyi)

## Confirmed public facts
- Institution: Chindwin Technological University, Taunggyi Campus.
- Published address: No.57/16, Myat Yadanar Street, Yae Aye Kwin Quarter, Taunggyi, Shan State, Myanmar.
- Official page reports 7,888 sq ft and four floors. This is a building/floor-area description, not a verified land parcel or campus AOI polygon.
- The official page's embedded Google Maps iframe resolves to a map center near 97.0485373 E, 20.7998693 N. This is a map center, not a surveyed campus boundary.

## AOI status: HOLD
Do not use the map center, address geocoder point, building footprint, or published floor area as a campus polygon. Obtain a boundary GeoJSON from an authorized campus representative or trace a proposed boundary against authoritative imagery and obtain written campus approval. Record approver, approval time, CRS (WGS84 / EPSG:4326), source, and version.

Suggested evidence fields: aoi_id, institution, campus_name, geometry, crs, boundary_source, boundary_version, approved_by, approved_at, approval_evidence_uri, created_at, sha256.

## Copernicus STAC catalogue
- Current migration target (announced 16 October 2026): https://stac.opensearch.dataspace.copernicus.eu/v1/
- Current parallel endpoint during migration: https://stac.dataspace.copernicus.eu/v1/
- Collection: sentinel-2-l2a
- Search endpoint: POST https://stac.opensearch.dataspace.copernicus.eu/v1/search
- Collection metadata confirms B04 (Red) and B08 (NIR) at 10 m GSD; SCL is 20 m.
- The new endpoint is scheduled to replace the old endpoint on 12 January 2027.

## Live regional discovery evidence (not campus AOI evidence)
A regional bounding-box query was executed against the new Copernicus STAC endpoint:
- Search envelope: bbox [97.00, 20.75, 97.10, 20.85] (longitude/latitude).
- Date interval: 2026-01-01T00:00:00Z/2026-10-31T23:59:59Z.
- Sentinel-2 L2A: numberMatched=280; first page returned 5 items.
- Sentinel-2 L1C: numberMatched=276; first page returned 5 items.
- Example returned L2A item IDs:
  - S2B_MSIL2A_20261028T035849_N0513_R004_T47QLD_20261028T074647
  - S2B_MSIL2A_20261028T035849_N0513_R004_T47QLC_20261028T074647
  - S2A_MSIL2A_20261025T040201_N0513_R004_T47QLD_20261025T073510
- Example returned L1C item IDs:
  - S2B_MSIL1C_20261028T035849_N0513_R004_T47QLD_20261028T073026
  - S2B_MSIL1C_20261028T035849_N0513_R004_T47QLC_20261028T073026
  - S2A_MSIL1C_20261025T040201_N0513_R004_T47QLD_20261025T055708
- These are regional catalogue matches from a provisional search envelope around the published map centre. They are not confirmed to intersect the campus boundary.
- The live response included a next-page link. Pagination is therefore required.
- No imagery has been downloaded, no NDVI has been calculated, and no campus-level environmental result is claimed.

## Implementation scope in this branch
- Structural WGS84 GeoJSON Polygon validation (closed rings and coordinate ranges).
- Copernicus STAC POST search using the new endpoint.
- Safe same-host pagination across all result pages.
- Client-side cloud-cover filtering; items without numeric cloud-cover metadata are excluded.
- Mocked unit tests for AOI validation, search payload, cloud filtering, pagination, and unsafe next-link rejection.
- CLI for catalogue discovery once an approved AOI is supplied.

## Not implemented / not verified
- Official campus boundary acquisition or approval.
- Campus-intersection STAC search.
- Satellite asset download and authentication.
- Raster decoding, cloud masking, NDVI calculation.
- Scientific review, OIA evidence-adapter integration.
- Production deployment.

## Run discovery after approval
    python scripts/earth_observation_discovery.py approved-campus-aoi.geojson --datetime 2026-01-01T00:00:00Z/2026-10-31T23:59:59Z --cloud-cover-max 30

The script reports catalogue items and asset keys. It does not download imagery, calculate NDVI, or prove vegetation condition.

## Decision gates
1. AOI approval: campus representative supplies or approves polygon.
2. Catalogue discovery: live STAC response archived with timestamp and request parameters.
3. Asset acquisition: B04/B08 assets downloaded and checksummed.
4. Processing: reflectance scaling, QA/SCL masking, raster alignment, NDVI.
5. Scientific QA: uncertainty, no-data, spatial representativeness and temporal comparability reviewed.
6. OIA admission: provenance and review evidence accepted by KMH OIA.
