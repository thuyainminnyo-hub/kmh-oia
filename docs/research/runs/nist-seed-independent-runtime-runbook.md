# KMH Independent Reproduction — GitHub Actions Runbook

**Status:** Planned; CI run not yet configured or observed  
**Primary source:** https://www.anthropic.com/research/ecdsa-curve-origins  
**Existing local reproduction record:** https://github.com/thuyainminnyo-hub/kmh-oia/blob/main/docs/research/runs/nist-ecdsa-seed-reproduction-2026-10-17.md

## Objective
Run Anthropic's published seed-reconstruction snippet in a separate Python runtime, capture the job log, and compare all 14 published seed strings.

## Proposed independent runtime
GitHub Actions hosted runner with Python 3.12.

## Required test
1. Copy the seed-reconstruction snippet and its published constants from Anthropic's primary source into a repository test script.
2. Add an assertion for each of the 14 expected strings.
3. Add a workflow that runs the script on pushes affecting the test and on manual dispatch.
4. Confirm the workflow run completed successfully.
5. Save the workflow URL, commit SHA, Python version, and exact test summary here and in the Notion case study.

## Acceptance criteria
- All 14 assertions pass in the hosted runner.
- The job log and commit are linkable.
- If any assertion fails, record FAIL and investigate; do not edit expected values just to force a pass.
- A successful CI run is an independent-runtime reproduction, but not a cryptographic audit or proof that every curve is free of weaknesses.

## Limitations
This runbook is not evidence that GitHub Actions has been configured or executed. Keep status **PLANNED** until a real workflow run is observed.
