# Pilot Architecture

## Placement in KMH OIA

The Creative Studio is a domain module/adapter under the KMH OIA governance boundary. It is not a second OIA core and does not bypass the existing runtime path:

`User Goal → Input Gateway → OIA Core → Context Assembly → Workflow → Agent → State → Tool Security → Governed Tool → Evaluation → Response → Trace`

## Phase 01 logical components

1. **Project Knowledge Adapter** — indexes only approved project code and documentation. Graphify is a candidate implementation, installed project-scoped after security and licensing review.
2. **Design Research Skills** — structures discovery, personas, journeys, problem framing, and evidence summaries. Designer Skills marketplace plugins are optional providers; the project skill specs remain the baseline.
3. **Design Contract** — `DESIGN.md` plus `contracts/design-contract.json`; the JSON contract is the machine-checkable token/accessibility source.
4. **Creative Output Providers** — UI code, prototypes, motion assets, presentation, and 3D outputs. Hallmark, Huashu, LottieFiles Motion Skill, and Blender Agent Skills remain provider adapters, not required runtime dependencies.
5. **QA Evidence Gate** — deterministic contract validation first, then browser/accessibility/device/user review as separate gates.
6. **Human Approval** — accepts design direction, cultural representation, character identity, and public release.

## Execution flow

`Brief → Approved Context → Research Summary → Design Direction → Design Contract → Prototype → Automated QA → Human Review → Release Decision`

Every output must carry a project ID, source references, tool/provider version, input contract version, generated artifact paths, QA results, reviewer decision, and timestamp in the production implementation. Phase 01 defines this record; it does not yet connect it to an external event store.

## Provider integration order

- Phase 01: local design contract + standard-library validator.
- Phase 02: Graphify project-scoped knowledge indexing with an explicit approved-path allowlist.
- Phase 03: install a minimal Designer Skills plugin set, after reviewing plugin manifests and skill contents.
- Phase 04: browser review/audit integration for the interactive studio prototype.
- Phase 05: Lottie motion and Blender 3D adapters, each with isolated fixtures and output QA.

## Non-goals

No automated garment reconstruction, no true shawl-alpha recovery from flattened artwork, no automatic character identity approval, no 3D garment mesh generation from a 2D PNG, no unattended production deployment.
