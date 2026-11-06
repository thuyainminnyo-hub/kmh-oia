---
name: kmh-design-system
description: Apply and maintain the KMH Creative Studio DESIGN.md and machine-readable design contract when designing or modifying UI components.
---

# KMH Design System

1. Read the nearest `DESIGN.md` and `contracts/design-contract.json` before changing UI.
2. Use semantic tokens; do not add ad-hoc colors, spacing, radii, or typography without documenting the reason.
3. Define responsive behavior and component states: default, hover, focus, pressed, selected, disabled, loading, and error as applicable.
4. Preserve Burmese/English text wrapping, line height, accessible names, keyboard order, and touch targets.
5. Respect `prefers-reduced-motion`; motion must communicate state or causality.
6. For MLCW, preserve approved character identity assets and protected regions; do not reconstruct missing source artwork without approval.
7. Run `python scripts/validate_design_contract.py` from the Creative Studio folder after changing the contract.

## Output contract

Return changed components, token references, responsive rules, interaction states, accessibility notes, and the validation result. State any browser/device checks not run.
