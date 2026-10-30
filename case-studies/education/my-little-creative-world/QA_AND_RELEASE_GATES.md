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
