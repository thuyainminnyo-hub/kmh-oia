# DhammaVerse Web Pilot — Manual Verification

## Preview
Serve this directory over HTTP (not file://), for example:
`python -m http.server 8000` from `apps/dhammaverse/web`.

## Checks
- [ ] Page loads at 360px, 390px, 768px and desktop widths.
- [ ] Language switch updates all labelled content between Burmese and English.
- [ ] Source links open in a new tab with noopener/noreferrer.
- [ ] Correct quiz answer sets progress to 100% and persists after reload.
- [ ] Incorrect answer does not mark lesson complete.
- [ ] Reflection saves only to this browser's localStorage; no server submission.
- [ ] Keyboard can reach all controls and focus is visible.
- [ ] Burmese glyphs render correctly on Android Chrome and target tablets.
- [ ] Service worker installs when served on localhost/HTTPS.
- [ ] Reload after first successful load with network disabled; cached shell remains available.\n- [ ] Navigate to an uncached route while offline; branded offline fallback appears.\n- [ ] Confirm missing CSS/JS assets are not incorrectly answered with HTML.\n- [ ] Update deployment and verify old cache is removed and new app shell activates.
- [ ] Clear site data and verify the app behaves correctly as a first visit.

## Known limitations
- No backend, accounts, cross-device sync, analytics or AI inference.
- No audio/video assets are included.
- Offline cache is limited to the local app shell; external source links require connectivity.
- This manual test plan is not evidence that tests have passed. Record device, browser, date, tester and result before release.
- This learning draft is not approved for public Dhamma publication until source, scholar, translation, age-appropriateness and rights gates pass.
