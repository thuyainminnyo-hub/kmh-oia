# External Tool Inventory and Rollout

**Review date:** 2026-11-02  
**Adoption status:** Research completed; third-party tools are not installed or executed by this pilot.

| Provider | Proposed responsibility | Current published capability reviewed | Pilot decision |
|---|---|---|---|
| Graphify — `Graphify-Labs/graphify` | Project-scoped knowledge graph over approved code/docs | Supports Claude Code and project-scoped installation; deterministic local AST pass for code, while semantic processing of PDFs/images/video may use the assistant model or configured API | Phase 02 candidate; require approved path allowlist and data-flow review |
| Designer Skills — `Owl-Listener/designer-skills` | Research, design systems, UI, interaction, critique and testing workflows | README describes five collections; design-practice collection documents plugin modules and commands | Phase 03 candidate; select only a small set of plugins after source/manifest review |
| Awesome DESIGN.md — `VoltAgent/awesome-design-md` | Reference library for studying public design-system patterns | Public `DESIGN.md` examples capture color roles, type rules, component styles, layouts, responsive behavior and agent guidance | Research-only; create KMH's own contract, do not impersonate source brands |
| Hallmark — `Nutlope/hallmark` | Optional UI composition and browser-based design audit workflow | Theme library and browser lint/review process are documented by the project | Later experiment; not a design approval authority |
| Huashu Design — `alchaincyf/huashu-design` | Optional prototypes, presentations, motion and infographics | README documents multiple candidate directions and export types | Later experiment; verify outputs and export quality before adoption |
| LottieFiles Motion Design Skill | Motion design principles and UI choreography | Skills describe timing, easing and motion principles for UI | Later experiment; still require reduced-motion and interaction QA |
| Blender Agent Skills — `EL4CTEO/blender-skills` | Optional 3D pipeline automation | README documents Blender modeling, UV, materials, rigging, animation and QA | Later experiment; requires Blender runtime, model assets and human review |

## Phase 02 — Graphify intake checklist

- [ ] Confirm repository owner approval and exact repository paths to index.
- [ ] Exclude `.env*`, credentials, keys, personal data, private learner files, raw face images, generated media, and local state folders.
- [ ] Inspect Graphify version, package source, dependency tree, license, hooks, scripts, and permissions.
- [ ] Install in a disposable test clone with project scope, not globally.
- [ ] Run indexing only on the approved allowlist.
- [ ] Inspect generated graph nodes/edges and test whether source references resolve to actual files/lines.
- [ ] Measure false links, missing edges, indexing completeness, and removal behavior.
- [ ] Approve or reject the provider before enabling it in any recurring workflow.

Candidate commands from the official Graphify README (not executed by this pilot):

```bash
uv tool install graphifyy
graphify install --project
graphify .
```

## Phase 03 — Designer Skills intake checklist

- [ ] Review marketplace manifest and selected plugin source, scripts, hooks, and permission declarations.
- [ ] Begin with a small selected set for the existing MLCW product: `visual-critique`, `prototyping-testing`, `design-systems`, and `design-ops`; add `design-research` only where discovery evidence is needed.
- [ ] Install only in a throwaway/local project after approval; do not install every collection by default.
- [ ] Run one non-sensitive test brief and compare the output against the KMH design contract.
- [ ] Log provider version, skill/command used, input, output, defects, and human decision.

Marketplace registration command from the project README (not executed by this pilot):

```text
/plugin marketplace add Owl-Listener/designer-skills
```

Marketplace registration only adds the source catalog; plugin selection and installation are separate steps in Claude Code.

## Phase 04+ — Visual, motion and 3D provider intake

Hallmark, Huashu, LottieFiles Motion Skill, and Blender Agent Skills are deferred until the base UI contract passes. Each provider requires an isolated sample, reproducible output, license/dependency review, human review, and explicit QA evidence before adoption.
