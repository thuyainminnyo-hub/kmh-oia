# KMH MediCore Orthopedics Body Map — Local Pilot

**Status:** Prototype on an isolated branch; no merge or deployment.
**Data boundary:** Synthetic-only. The service is local SQLite; the static UI has no network or persistent browser-storage calls.
**Reference boundary:** Inspired by the general body-region annotation workflow in a user-provided screenshot; implementation and terminology are original.

## Selected pilot scenario

- Specialty: Orthopedics
- View: Front
- Region: Skull (SKULL, local registry version KMH-ANATOMY-LOCAL-0.2)
- Finding: Fracture
- Treatment: Cast or splint — **proposed only**, not recommended or marked performed
- Annotation status: Draft

This is a workflow fixture, not a clinical recommendation. In particular, selecting “cast or splint” for a skull finding does not imply that treatment is appropriate. Clinical assessment and treatment decisions belong to a qualified clinician.

## Files

- `schemas/medicore/body-map-annotation-0.1.schema.json`: initial schema proposal retained for history.
- `schemas/medicore/body-map-annotation-0.2.schema.json`: current annotation schema bound to registry version 0.2.
- `pilots/kmh_medicore_bodymap/service.py`: standard-library validation and local SQLite persistence; loads the versioned registry from the local filesystem.
- `pilots/kmh_medicore_bodymap/anatomy_registry.v0.2.json`: versioned local anatomy registry contract. Illustrative only, not a clinical terminology.
- `pilots/kmh_medicore_bodymap/ui/body-map-pilot.html`: standalone offline interaction prototype. The silhouette is schematic; it is not anatomically precise and is not connected to the Python service.
- `tests/test_kmh_medicore_bodymap.py`: scenario, registry loading, fail-closed version check, access-denial, audit-minimization, duplicate-record, and append-only audit tests.
- `tests/test_kmh_medicore_anatomy_registry.py`: schema/registry version alignment, enum alignment, unique codes/labels, view/laterality constraints, and non-clinical-authority disclaimers.
- `tests/test_kmh_medicore_bodymap_ui.py`: static UI checks for offline operation, the selected default scenario, region controls, and no-save messaging.

## Local test commands

```bash
python -m unittest tests.test_kmh_medicore_bodymap tests.test_kmh_medicore_anatomy_registry tests.test_kmh_medicore_bodymap_ui -v
python -m unittest discover -s tests -v
```

The pilot database is created only at the caller-supplied local path. The store uses a caller-provided allowlist of synthetic actor references; this is a test boundary, not a production identity provider. Audit events contain action/outcome, actor reference, timestamp, and correlation reference, but not the finding, treatment, or encounter reference. SQLite triggers prevent ordinary updates/deletes of audit rows.

## Known limits

- The HTML UI is a local interaction prototype only: it uses a schematic silhouette, has no anatomical precision, has no backend connection, and does not save drafts.
- Anatomy codes are local illustrative codes, not validated against an authoritative clinical terminology.
- The implementation supports draft creation and authorized reads only. Signing, amendments, delete flows, terminology integration, and clinical decision support are not implemented.
- SQLite append-only triggers are a local integrity control, not tamper-proof or externally immutable audit storage.
- No clinical safety, privacy compliance, production readiness, or integration compatibility is claimed.
