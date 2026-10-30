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


## Repository integration boundary (verified for PR #175)

The current PR commits project documentation only. The repository directory does not yet contain the runnable web app, package manifest, Playwright configuration, test files, or image assets. Therefore a product-specific Playwright workflow must not be added as if it can run against committed product code.

### Required before enabling product CI

1. Commit the runnable app and its referenced assets under a dedicated app directory.
2. Add a lockfile and Playwright test suite targeting that directory.
3. Add a workflow scoped to changes in that app directory and its workflow/test files.
4. Run the workflow and retain HTML report, screenshots and traces as artifacts.
5. Record the exact workflow run URL, head SHA, job conclusions and artifact links.

Until those prerequisites exist, the KMH OIA repository workflows validate the KMH OIA repository only; they do not prove the MLCW user interface works.


## Dependency automation readiness — 2026-10-31

- `.github/dependabot.yml` is committed on this PR branch, but Dependabot version-update monitoring starts only after the configuration is present on the repository default branch.
- GitHub Actions dependencies are configured for weekly checks at the repository root.
- The npm ecosystem entry is intentionally deferred because this repository branch does not yet contain the MLCW `package.json` or `package-lock.json`.
- Add the npm entry only after the manifest and a generated, committed lockfile are present in `/case-studies/education/my-little-creative-world`.
- Do not claim Dependabot is active from a PR-branch-only configuration.

Source: https://docs.github.com/en/code-security/concepts/supply-chain-security/about-the-dependabot-yml-file

## Current PR checkpoint — 2026-10-31

- PR #175 remains OPEN / DRAFT.
- Current branch head at this checkpoint: `c0d91640c24956947de5be3b1d323b452e2c25f8`.
- The Dependabot config correction was committed and fetched back for content verification.
- No workflow run was returned for that exact commit at the time of this checkpoint; do not infer a CI result.
- Product app integration, npm lockfile and product E2E remain pending/not run.
