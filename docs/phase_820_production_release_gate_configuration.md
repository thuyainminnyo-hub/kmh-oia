# Phase 820 — Production Release-Gate Configuration Lock

Date: 2026-10-22

## Change

- Added an explicit `runtime_environment` setting to `ProductionEvidenceRuntimeConfig`, restricted to production, staging, test, development or local.
- Production and staging configurations cannot set `require_signed_release_bundle=False`. A missing signed bundle therefore remains a startup failure, and disabling the gate is rejected during config validation before creating the evidence replay store.
- Updated 18 unit-test construction sites to declare `runtime_environment="test"` when deliberately using the unsigned local fixture mode.
- Repaired the production-startup-by-default test so it is defined inside the test class and is actually discoverable by unittest; added tests that production/staging cannot disable the gate and that unknown environment values are rejected.

## Trust boundary

The environment value is deployment configuration, not cryptographic evidence. Deployment configuration and public trust-root provisioning still need independent review. Even a signed, verified source bundle is not proof that production deployment or provider authenticity has been independently established.

**Production HOLD.** PR #97 remains OPEN / DRAFT / UNMERGED.
