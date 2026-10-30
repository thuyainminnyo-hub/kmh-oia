# My Little Creative World — Myanmar Traditional Princess

## Project passport

- Product ID: `MLCW-MYANMAR-001`
- Character: Thiri (သီရိ)
- Character ID: `MLCW-CHAR-001`
- Target age: 7–9
- Languages: Myanmar + English
- Prototype version: 1.0.1
- Repository integration: KMH OIA case-study / isolated creative-learning pilot
- Status: prototype source and QA plan prepared; CI, physical-device QA, cultural review and deployment are not yet verified.

## Purpose

A bilingual paper-doll and creative-learning prototype that introduces children to stylized interpretations of Myanmar clothing through outfit selection, pattern exploration, drawing and storytelling.

This pilot is intentionally isolated from the existing Education Business OS operational workflows. It does not process student enrolments, payments, attendance or other education-business records.

## Deliverables

- Original Thiri character illustration.
- Ten outfit concept assets.
- Outfit selection UI with tap-to-select.
- Reset action.
- User-triggered PNG export.
- Local-only prototype; no user accounts, analytics or personal-data collection.
- Playwright test plan and axe-core accessibility scan configuration.
- Firebase Hosting configuration for a future preview channel.

## Asset registry

| Asset ID | Description | Current state |
|---|---|---|
| MLCW-CHAR-001 | Thiri character | Generated base illustration |
| MLCW-OUTFIT-001 | Pink wave motif | Extracted concept crop |
| MLCW-OUTFIT-002 | Teal and sky blue | Extracted concept crop |
| MLCW-OUTFIT-003 | Gold and maroon | Extracted concept crop |
| MLCW-OUTFIT-004 | Lavender | Extracted concept crop |
| MLCW-OUTFIT-005 | Indigo and gold | Extracted concept crop |
| MLCW-OUTFIT-006 | Forest green | Extracted concept crop |
| MLCW-OUTFIT-007 | Coral and brown | Extracted concept crop |
| MLCW-OUTFIT-008 | Cream and indigo | Extracted concept crop |
| MLCW-OUTFIT-009 | Festival pink | Extracted concept crop |
| MLCW-OUTFIT-010 | Royal cream and gold | Extracted concept crop |

**Known asset limitation:** the current clothing PNGs are crops from one composite concept sheet. They are not independently illustrated, fitted garment layers. Precise garment-to-body alignment, edge cleanup and transparent cutout quality remain open QA work. The current overlay behavior is a visual interaction demonstration, not a production-grade dress-up engine.

## Architecture

```text
Static Web UI
  ├── Character base asset
  ├── Outfit concept assets
  ├── Tap-to-select controller
  ├── Reset controller
  └── User-triggered PNG export

Storage: browser memory only
Accounts: none
Analytics: none
Backend: none in this prototype
Future hosting: Firebase Hosting preview channel, after approval
```

## Accessibility requirements

- All outfit choices must be keyboard reachable and operable.
- Outfit choice state must be programmatically exposed (for example, `aria-pressed`).
- Provide tap/click selection as a non-drag alternative.
- Ensure visible keyboard focus and meaningful accessible labels.
- Target at least 44 × 44 CSS px for key controls as a usability target; assess WCAG 2.2 AA minimum target-size requirements separately.
- Automated axe-core scanning is supplemental; manual screen-reader and keyboard testing remain mandatory.

## QA plan and evidence status

| Test | Acceptance criteria | Status |
|---|---|---|
| Static source validation | HTML/JS/config parse correctly | Limited static checks reported in working session; re-run in CI |
| E2E load | Studio loads and ten outfit choices appear | Not run |
| Outfit selection | Selecting an outfit updates state and announcement | Not run |
| Reset | Reset restores base character and clears selection | Not run |
| Keyboard | Outfit buttons can be focused and activated | Not run |
| Mobile viewport | Controls remain visible at small viewport | Not run |
| axe-core | No serious/critical automated findings | Not run |
| Real Android/iOS | Test on actual devices and browsers | Not run |
| Export | PNG output visually checked and dimensions confirmed | Not run |
| Garment alignment | Each garment aligns with character | Blocked by composite concept asset quality |
| Cultural review | Knowledgeable reviewer approves descriptions and depictions | Pending |
| Rights review | Asset provenance and commercial-use rights documented | Pending |
| Child/teacher pilot | Supervised usability testing with appropriate permissions | Pending |

Do not infer CI PASS from a workflow file or test suite being committed. Record exact workflow run, commit SHA, job outcome and artifacts before changing any status to PASS.

## Child privacy and safeguarding

- No child account or personal data is required for the first prototype.
- Do not add advertising, public sharing, telemetry or behavioural profiling.
- Use synthetic test data only.
- Conduct parent/guardian and teacher review before any child pilot.
- Supervise scissor use in the associated printable craft activity.
- Obtain appropriate permissions and assess applicable privacy and child-safety requirements before external release.

## Release gates

1. Replace concept-sheet crops with properly separated and aligned garment layers.
2. Run Playwright CI and inspect test report.
3. Run axe-core and manual keyboard/screen-reader checks.
4. Test PNG export and actual mobile devices.
5. Complete Myanmar cultural review.
6. Complete asset provenance and rights review.
7. Complete privacy/safeguarding review.
8. Approve Firebase preview publication; treat preview URLs as potentially public.
9. Obtain explicit release approval before production deployment.

## Decision

**GO for isolated prototype iteration. HOLD for public/production release.**

This package is a prototype and implementation plan. It is not a verified classroom product, certified toy, live Firebase deployment, or commercially approved product.
