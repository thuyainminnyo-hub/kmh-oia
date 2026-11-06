# KMH Earth Observation Pilot V1 — Real Product First

**Product goal:** deliver one defensible, useful environmental monitoring report for the Chindwin Taunggyi campus before expanding into a reusable platform.

## Product promise (V1)

After campus authorization and successful acquisition, V1 will provide:
- a dated satellite observation record for the approved campus AOI and its stated spatial context;
- a clear cloud/no-data and spatial-resolution quality assessment;
- a vegetation indicator only when suitable imagery and scientific QA support it;
- a human-reviewed report with source IDs, acquisition dates, uncertainty and limitations.

V1 does not promise parcel-scale vegetation measurement from 10 m imagery. If the approved campus area is too small or mixed pixels dominate, the product must report that the satellite is unsuitable for the requested campus-level claim and recommend permissioned ground observations instead.

## Scope lock

**In scope:** one campus, one approved AOI, Sentinel-2 catalogue discovery, asset availability review, one baseline observation/report, provenance and human QA.

**Out of scope:** global monitoring, multi-campus tenancy, predictive climate claims, automated policy decisions, public dashboards, and production deployment until the V1 report passes acceptance.

## Release gates

1. **AOI authorization:** receive campus-authorized polygon and evidence. A map pin, address, building footprint or floor area is not a boundary.
2. **Catalogue discovery:** run the exact AOI against Copernicus STAC; archive request, response metadata, timestamp, collection, item IDs and cloud cover. Zero items is a valid result.
3. **Asset acquisition:** obtain required bands/assets, verify HTTP status, file size, raster metadata and SHA-256. Never report a catalogue hit as a downloaded image.
4. **Processing:** confirm product level, reflectance scaling, band alignment, cloud/shadow masking and no-data handling before computing an index.
5. **Scientific QA:** assess pixel count, mixed-pixel risk, cloud contamination, temporal comparability, uncertainty and ground evidence.
6. **Human review:** reviewer signs the report and its limitations.
7. **Release:** publish only after security, backup, monitoring and deployment evidence are independently verified.

## Current AOI policy

Chindwin AOI status remains **HOLD / NEEDS_CAMPUS_EVIDENCE**. The discovery CLI now requires a GeoJSON Feature with approval metadata and a matching geometry SHA-256. This is an integrity and completeness gate, not independent authentication of the approver. Approval evidence must be checked by a human before the record is marked APPROVED.

## Technical sequence

- [x] Initial Sentinel-2 L2A STAC client scaffold
- [x] Mocked STAC unit tests
- [x] GitHub Actions validation workflow
- [x] AOI approval metadata + geometry fingerprint gate
- [ ] Live regional/approved-AOI STAC discovery evidence
- [ ] Authorized campus AOI supplied and independently reviewed
- [ ] Asset download + checksum manifest
- [ ] Raster processing + cloud mask + vegetation index tests
- [ ] Human-reviewed baseline report
- [ ] Production deployment and runtime evidence

## Copernicus endpoint lifecycle

The current STAC endpoint is documented at `https://stac.dataspace.copernicus.eu/v1/`. Copernicus announced a new SFEOS endpoint at `https://stac.opensearch.dataspace.copernicus.eu/v1`, available alongside the current endpoint until 12 January 2027. Keep the base URL configurable and test both endpoints before migration; do not silently switch without contract tests.

References:
- https://documentation.dataspace.copernicus.eu/APIs/STAC.html
- https://dataspace.copernicus.eu/news/2026-10-16-new-sfeos-stac-catalogue-endpoint
