# KMH Earth Observation Pilot V1 — Myanmar Land Change

## Product objective
Produce reproducible, evidence-backed land-change assessments for a user-selected area in Myanmar by comparing two Sentinel-2 Level-2A observations.

## V1 scope
- AOI (area of interest) supplied as GeoJSON polygon.
- Discover Sentinel-2 L2A scenes through the Copernicus Data Space Ecosystem (CDSE) STAC catalogue.
- Filter by date range, cloud cover and AOI intersection.
- Record source item IDs, acquisition timestamps, processing baseline and asset references.
- Generate a cloud-masked, co-registered comparison using a documented spectral-index / classification method.
- Produce before/after previews, a change raster, area statistics and a machine-readable QA report.
- Human review is required before an alert is marked verified.

## Explicit non-goals
- No trading or financial execution.
- No autonomous land ownership, legal-boundary or enforcement claims.
- No inference of intent from land-cover change.
- No claim that a detected spectral change proves deforestation, construction or illegal activity without corroborating evidence.
- No live public alerting in V1.

## Proposed stack
- API: Python 3.12, FastAPI, Pydantic
- Database: PostgreSQL + PostGIS; object storage for source/derived rasters
- Geospatial: GDAL, Rasterio, GeoPandas, Shapely, xarray as needed
- Catalogue: CDSE STAC API; Sentinel-2 L2A
- UI: React / TypeScript map dashboard (implementation decision can be revised)
- Tests: pytest, API contract tests, geospatial fixture tests

## Pipeline
1. Validate AOI geometry (WGS84, valid polygon, bounded area).
2. Search CDSE STAC for two comparable date windows.
3. Reject scenes failing cloud-cover / coverage / temporal criteria.
4. Download or stream required assets; preserve immutable source metadata.
5. Reproject, align grids, mask clouds / cloud shadows, and compute indices.
6. Compare observations and generate candidate change classes.
7. Run QA: coverage, cloud contamination, registration, valid pixels, thresholds, provenance.
8. Store outputs and audit events.
9. Human reviewer approves, rejects or requests reprocessing.
10. Render map, statistics and downloadable report.

## Data model (initial)
- areas_of_interest: id, name, geom, created_at
- satellite_scenes: id, provider, collection, item_id, acquired_at, cloud_cover, footprint, metadata_json, asset_manifest
- analysis_runs: id, aoi_id, baseline_scene_id, comparison_scene_id, status, parameters_json, started_at, completed_at
- artifacts: id, run_id, artifact_type, object_uri, checksum, metadata_json
- qa_checks: id, run_id, check_name, status, measured_value, threshold, details_json
- review_decisions: id, run_id, reviewer, decision, notes, created_at
- audit_events: id, run_id, event_type, actor, payload_json, created_at

## QA acceptance gates (initial targets; tune with pilot validation)
- AOI geometry valid and within supported processing bounds.
- Both scenes intersect at least 95% of the AOI.
- Cloud / shadow contamination within configured threshold; default target <= 20% over AOI after masking.
- Co-registration error within configured tolerance; default target <= 1 pixel where measurable.
- At least 80% valid comparable pixels after masks.
- Every output has source item IDs, timestamps, parameters, software version and checksums.
- No result is marked verified without a human review decision.

Thresholds are configuration, not universal scientific guarantees. Report failures explicitly; do not silently lower thresholds.

## Evidence required to claim a real run
- CDSE catalogue response / item IDs and acquisition metadata.
- Source asset manifest and checksums.
- API request and response IDs.
- Processing logs with software and parameter versions.
- Before/after and output artifact checksums.
- QA report with pass/fail reasons.
- Human review record.
- Reproducible run ID.

## Current implementation status
This branch contains the initial product specification and is not yet a deployed or executed satellite-processing system. No satellite scenes have been fetched and no land-change result has been verified yet.
