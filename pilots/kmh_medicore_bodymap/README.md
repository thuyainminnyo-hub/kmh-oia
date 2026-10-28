# KMH MediCore Orthopedics Body Map — Local Pilot

**Status:** Prototype on an isolated branch; no merge or deployment.
**Data boundary:** Synthetic-only. No external API calls or real patient data.
**Reference boundary:** Inspired by the general body-region annotation workflow in a user-provided screenshot; implementation and terminology are original.

## Selected pilot scenario

- Specialty: Orthopedics
- View: Front
- Region: Skull (SKULL, service annotation schema v0.1)
- Finding: Fracture
- Treatment: Cast or splint — **proposed only**, not recommended or marked performed
- Annotation status: Draft

This is a workflow fixture, not a clinical recommendation. In particular, selecting “cast or splint” for a skull finding does not imply that treatment is appropriate. Clinical assessment and treatment decisions belong to a qualified clinician.

## Files

- `schemas/medicore/body-map-annotation-0.1.schema.json`: machine-readable annotation schema.
- `pilots/kmh_medicore_bodymap/service.py`: standard-library validation and local SQLite persistence.
- `pilots/kmh_medicore_bodymap/anatomy_registry.v0.2.json`: versioned local anatomy registry contract for region labels, views, and laterality. This is illustrative and not a clinical terminology.
- `tests/test_kmh_medicore_bodymap.py`: scenario, validation, access-denial, audit-minimization, duplicate-record, and append-only audit tests.
- `tests/test_kmh_medicore_anatomy_registry.py`: registry/schema enum alignment, unique codes/labels, view/laterality constraints, and non-clinical-authority disclaimers.

## Local test commands

```bash
python -m unittest tests.test_kmh_medicore_bodymap tests.test_kmh_medicore_anatomy_registry -v
python -m unittest discover -s tests -v
```

The pilot database is created only at the caller-supplied local path. The store uses a caller-provided allowlist of synthetic actor references; this is a test boundary, not a production identity provider. Audit events contain action/outcome, actor reference, timestamp, and correlation reference, but not the finding, treatment, or encounter reference. SQLite triggers prevent ordinary updates/deletes of audit rows.

## Known limits

- The visual interactive anatomy map is not implemented yet; this increment adds a versioned registry contract and tests.
- The service annotation schema is v0.1 while the separate registry contract is v0.2; explicit integration/migration is still needed.
- Anatomy codes are local illustrative codes, not validated against an authoritative clinical terminology.
- The implementation supports draft creation and authorized reads only. Signing, amendments, delete flows, terminology integration, and clinical decision support are not implemented.
- SQLite append-only triggers are a local integrity control, not tamper-proof or externally immutable audit storage.
- No clinical safety, privacy compliance, production readiness, or integration compatibility is claimed.
