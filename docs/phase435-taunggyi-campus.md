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

## Live point-based Sentinel-2 discovery (6 November 2026; not an AOI approval)
A second live query used a very small bbox around the campus page's published map centre (97.0485373 E, 20.7998693 N), solely to identify catalogue granules whose bounding boxes cover that point. This is not a campus boundary or campus intersection query.
- Query envelope: [97.0484, 20.7997, 97.0487, 20.8000].
- Date interval: 2026-01-01T00:00:00Z/2026-11-06T23:59:59Z.
- L2A: numberMatched=71; 10 first-page records inspected.
- L1C: numberMatched=70; 10 first-page records inspected.
- Candidate L2A item: S2A_MSIL2A_20261025T040201_N0513_R004_T47QKD_20261025T073510.
- Acquisition time: 2026-10-25T04:02:01.024Z.
- Catalogue cloud cover: 18.48%.
- Item bbox: [96.16191776596, 20.687816199722505, 97.17354773867191, 21.69322169612896]. A point-in-polygon check against the exact STAC item geometry also returns true for the published map centre (97.0485373 E, 20.7998693 N). This proves only that the published map centre lies inside the satellite granule footprint, not that the campus boundary is covered.
- Required catalogue assets are present: B04_10m (99,407,518 bytes), B08_10m (122,516,278 bytes), SCL_20m (1,601,158 bytes), each with a catalogue checksum.
- The scene-level SCL summary reports 10.97% high-probability cloud, 7.48% medium-probability cloud, 7.48% cloud shadows, and 15.81% no-data. These are whole-scene statistics, not campus statistics.
- A newer candidate on 2026-11-02 had 26.38% catalogue cloud cover and higher cloud/shadow/no-data fractions in its whole-scene SCL summary. The 25 October candidate is therefore the better initial metadata candidate, but requires raster inspection before acceptance.
- The 25 October scene's asset bytes have NOT been downloaded. No checksum has been recomputed locally, no campus polygon intersection has been established, and no NDVI result has been generated.

## Asset access and authentication
The STAC item advertises B04/B08/SCL assets with S3 storage references and HTTPS alternate locations using OIDC authentication. Public catalogue metadata does not imply that the underlying raster bytes are anonymously downloadable. Use a registered Copernicus account/client and securely managed credentials for acquisition; never commit secrets to GitHub.

## Additional implementation in this branch
- Fail-closed campus AOI approval-record validator requiring APPROVED status, approver, timestamp, HTTPS evidence URI, EPSG:4326 and matching geometry SHA-256.
- Required L2A asset metadata validator for B04_10m, B08_10m and SCL_20m, including data role, GSD, positive size and catalogue checksum.
- Unit tests for approval rejection, geometry hash mismatch, required asset presence and resolution/checksum validation.

These validators establish record completeness only. They do not independently authenticate campus authority, verify downloaded file bytes, or constitute scientific approval.

- Campus-specific discovery wrapper: `search_approved_campus_aoi(record, datetime_range, ...)` validates the complete AOI approval record before invoking STAC; pending or malformed approval is rejected before any network request.
