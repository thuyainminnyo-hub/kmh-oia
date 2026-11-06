---
name: kmh-design-qa
description: Review creative-studio interfaces and generated assets against the KMH design contract, accessibility criteria, identity constraints, and evidence gates.
---

# KMH Design QA

1. Read the feature requirements, `DESIGN.md`, JSON design contract, and protected-asset requirements.
2. Run the deterministic contract validator and relevant unit tests.
3. Inspect screenshots at mobile and desktop widths; record viewport dimensions and browser version.
4. Check keyboard reachability, visible focus, accessible names, text contrast, reduced motion, responsive wrapping, and status announcements.
5. For MLCW, compare protected face/hair/skin/accessory regions against approved source evidence; do not infer identity preservation from a design screenshot alone.
6. Record each finding with severity, screenshot/path, reproduction steps, expected result, and observed result.
7. Mark unrun checks `NOT RUN` and incomplete evidence `PENDING`; do not promote the release gate.

## Output contract

Return a QA matrix with `PASS`, `FAIL`, `BLOCKED`, or `NOT RUN`, evidence references, defects, risks, and a release recommendation.
