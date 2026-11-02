# KMH Creative Intelligence & Design Studio V1

**Status:** Pilot Phase 01 — foundation package created; external tools not installed or executed.

## Purpose

A governed creative-design capability for KMH OIA. The studio combines project knowledge retrieval, design research, reusable design tokens, UI/interaction skills, and evidence-based QA. It is an isolated case-study module and does not modify the KMH OIA runtime core.

## First pilot target

**My Little Creative World (MLCW) — Creative Studio UX foundation.** The initial deliverable is the design contract and review workflow for the future interactive outfit-selection studio. It does not claim to repair P01 garment assets, recover true shawl alpha, render 3D garments, or certify a production UI.

## Pilot Phase 01 deliverables

- `DESIGN.md` — KMH-authored visual and interaction rules; not copied from another brand.
- `contracts/design-contract.json` — machine-readable tokens and accessibility constraints.
- `scripts/validate_design_contract.py` — dependency-free validator for required tokens and contrast floors.
- `tests/test_design_contract.py` — synthetic unit tests for valid and invalid contracts.
- `agent-skills/` — three project-specific skill specifications for research, design-system use, and QA. These are reference specifications; they are not automatically installed or activated in Claude Code.
- `docs/architecture.md`, `docs/security-and-governance.md`, `docs/phase-01-acceptance.md` — boundaries, safe rollout, and acceptance gates.

## Architecture boundary

`KMH OIA Core → Creative Studio Adapter → Research / Design System / UI / Motion / 3D Providers → QA Evidence → Human Approval`

In Phase 01, only the deterministic design-contract validation is executable. Graphify, Designer Skills marketplace plugins, Hallmark, Huashu, LottieFiles Motion Design Skill, and Blender Agent Skills remain optional external adapters pending review and approval.

## Local validation

From this directory:

```bash
python -m unittest discover -s tests -v
python scripts/validate_design_contract.py
```

Both commands use the Python standard library only.

## What is not claimed

- No third-party marketplace plugin or external skill has been installed.
- Graphify has not been run against private KMH or MLCW files.
- No Claude Code session, browser audit, Blender session, or motion-render execution has been performed.
- No deployed UI, user study, production release, or commercial readiness is claimed.
