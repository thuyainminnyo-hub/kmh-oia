# GOLDEN PALACE — Synthetic EPCIS Traceability Pilot

**Status:** isolated implementation pilot; synthetic fixtures only.  
**Profile:** OIA-local synthetic traceability contract; not CBV-Compliant and not production-ready.

## Safety boundary

- No production data, credentials, supplier systems, stock mutation, or external communications.
- Mock recall is a draft simulation only.
- No merge, deployment, or promotion is authorized by this pilot.
- Existing PR #185 and PR #216 are out of scope and must remain untouched.

## Scope of this first slice

- Load a deterministic synthetic receiving fixture.
- Validate the OIA-local source envelope before mapping.
- Adapt the source into an EPCIS-shaped ObjectEvent representation.
- Preserve provenance and explicitly mark all identifiers as synthetic.
- Keep EPCIS structural validation, JSON-LD/SHACL validation, and independent business-oracle checks as separate gates.

## Important conformance limitation

This initial adapter does **not** embed the official GS1 EPCIS 2.0.1 JSON Schema, JSON-LD context, CBV artefacts, or SHACL shapes. It therefore does not claim EPCIS 2.0.1 conformance or CBV compatibility. Official artefacts must be captured as exact upstream bytes and SHA-256 pinned before those validation gates can be enabled. Local IDs are not GS1 identifiers and must not be represented as allocated GS1 EPCs.

## Run

```bash
python -m unittest tests.test_golden_palace_epcis -v
```

## Promotion gates

1. Official GS1 EPCIS 2.0.1 / CBV 2.0.0 artefacts pinned by exact-byte SHA-256.
2. JSON Schema validation passes.
3. JSON-LD processing uses a local vetted context only.
4. SHACL validation passes against the pinned shapes.
5. Independent oracle confirms event ordering, quantity conservation, and lot lineage.
6. Human review approves the evidence bundle.

All gates above are currently pending except the local fixture/adapter unit tests, which must be run in an execution environment before they can be marked PASS.
