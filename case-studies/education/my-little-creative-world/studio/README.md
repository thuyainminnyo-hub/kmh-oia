# My Little Creative World — Thiri Outfit Studio V1.0.2

Local-first bilingual (Myanmar + English) creative-learning prototype for ages 7–9.

## Run
Run npm install, npm test, npx playwright install chromium, npm run test:e2e, then npm start and open http://localhost:4173.

## Implemented
- Canonical Thiri artwork asset, ID MLCW-CHAR-001.
- Ten bilingual outfit choices with stable registry IDs.
- SVG blouse/htamein colour and motif preview layers.
- Reset to base outfit and local 1024×1536 PNG export.
- Keyboard-operable controls, aria-pressed, live status and responsive layout.
- Node unit tests and Playwright browser tests.
- No accounts, analytics, telemetry or child personal-data collection.

## Limitations / release gate
The ten designs are stylized colour/pattern overlays, not final fitted garment cutouts or historically authoritative costumes. Overlay geometry requires visual review. Product-specific browser tests are committed but not yet run in GitHub Actions. Printable PDF QA, accessibility audit, physical-device testing, cultural review, rights review, parent/teacher review and supervised learner testing remain pending. No Firebase deployment or commercial release is claimed. Prototype iteration only; public release remains HOLD.