# Chindwin Taunggyi Campus AOI Approval Pack

Status: NEEDS_CAMPUS_EVIDENCE
AOI ID: MM-SHN-TAUNGGYI-CHINDWIN-CAMPUS-001
Pilot: KMH Earth Observation Pilot V1 / Phase 435.2

## Purpose

Prepare a defensible Area of Interest (AOI) for environmental monitoring of the Chindwin Taunggyi campus. This document does not define or imply a campus boundary. No polygon may be used for live satellite intersection until the campus-authorized boundary is received, checked, and approved.

## Known reference information

- Official campus address: No.57/16, Myat Yadanar Street, Yae Aye Kwin Quarter, Taunggyi, Shan State, Myanmar.
- Official campus page: https://ctu.edu.mm/taung-gyi-campus/
- Provisional map centre previously recorded: 20.7998693 N, 97.0485373 E. This is a locator only, not a boundary vertex or surveyed control point.
- The campus page describes 7,888 sq ft (58 ft x 34 ft) across four floors. Do not treat this building/floor-area description as a parcel area.

## Required evidence

1. Campus-authorized site plan, parcel map, or a boundary walk supervised by an authorized representative.
2. Written confirmation identifying included, excluded, shared, leased, or otherwise non-campus areas.
3. Name and role of approving representative, approval date, and contact channel.
4. Boundary source and method: official plan, survey, or GPS field capture; include survey date and estimated positional accuracy if known.
5. GeoJSON Polygon or MultiPolygon exported in WGS 84 longitude/latitude (RFC 7946), with source document retained separately.
6. Review record confirming the polygon overlay matches the authorized plan or surveyed perimeter.

If no digital polygon exists, KMH may prepare a draft by digitizing the supplied site plan or supervised field observations. Mark it PROPOSED_NOT_APPROVED. Do not use it for production Copernicus STAC search.

## Boundary capture procedure

1. Obtain permission before entering, photographing, or surveying campus property.
2. Ask the representative to walk the perimeter and identify gates, walls, parcel corners, shared edges, and excluded areas.
3. Record GNSS/GPS points at every change of direction and identifiable corner; record device, date/time, coordinate format, and estimated accuracy.
4. Capture a track or photographs only with permission. Do not infer obscured boundaries from roofs, shadows, roads, or vegetation.
5. Digitize the supplied plan/points in QGIS. Preserve the original source unchanged.
6. Export GeoJSON Polygon/MultiPolygon using WGS 84 longitude/latitude. Coordinate order is longitude, latitude.
7. Compare the overlay with the source plan and obtain written approval of the final rendered polygon.

## Geometry and provenance validation

- Geometry type is Polygon or MultiPolygon.
- Exterior rings contain at least four positions and are closed.
- Coordinates are finite and within longitude [-180, 180], latitude [-90, 90].
- Coordinate order is longitude, latitude; no undocumented CRS transformation.
- Geometry is valid: no self-intersections, collapsed rings, or unintended holes.
- Calculate area in an appropriate projected CRS, not directly in square degrees.
- Record geometry SHA-256, file name, version, timestamp, source, author, reviewer, and approval record.
- Preserve original site plan and raw survey observations with access controls.

## Approval record template

- AOI ID and version:
- Campus/site name:
- Boundary source (site plan / survey / other):
- Source document reference:
- Survey/digitization date:
- Source CRS:
- Export CRS: WGS 84 / RFC 7946:
- Included areas:
- Excluded/shared/leased areas:
- Estimated positional accuracy:
- Prepared by:
- Reviewed by:
- Campus approver name and role:
- Approval date:
- Approval evidence reference:
- Geometry SHA-256:
- Decision: PROPOSED / APPROVED / REJECTED:
- Notes and conditions:

## Data model proposal

planetary/{regionId}/geographicAreas/{aoiId}

- geometry: GeoJSON
- geometryVersion: string
- status: PROPOSED | APPROVED | REJECTED | SUPERSEDED
- sourceType: SITE_PLAN | GNSS_SURVEY | OTHER
- sourceReference: string
- sourceCrs: string
- outputCrs: OGC:CRS84
- preparedBy / reviewedBy / approverRole
- approvedAt: timestamp or null
- geometrySha256: string
- positionalAccuracyM: number or null
- includedAreas / excludedAreas: string arrays
- auditEventIds: string array

Minimize personal data. Store approval evidence in restricted storage and reference it by ID.

## Release gate for live STAC discovery

Live campus-intersection search is blocked unless all are true:
- status is APPROVED;
- approver and approval evidence are recorded;
- geometry passes topology and coordinate validation;
- AOI version and SHA-256 are immutable and recorded;
- reviewer confirms the AOI represents the intended monitoring area.

After approval, run a bounded Copernicus Sentinel-2 L2A STAC query, preserve the exact request and response metadata, record query time and item IDs, and report zero results as a valid outcome.

## Scientific limitation

Sentinel-2 has 10 m, 20 m, and 60 m bands. A small campus or building footprint may be smaller than, or mixed within, one pixel. Do not claim parcel-scale vegetation measurements solely from Sentinel-2. Use satellite observations for surrounding context and regional trends; use permissioned ground observations for small campus features.

## Current status

NEEDS_CAMPUS_EVIDENCE. No approved polygon exists in this pack. No campus-specific STAC intersection, image download, NDVI result, or production deployment is claimed.