# KMH Case Study — Argo CD GitOps Image Update Automation

**Record type:** Case-study analysis and implementation proposal  
**Date:** 2026-10-18  
**Status:** Research / Draft — not deployed or tested in a Kubernetes cluster  
**Evidence status:** Source material supplied by user; technical mapping is a proposal, not independent verification of the video.

## 1. Executive summary
The workflow separates Continuous Integration (CI) from GitOps-based delivery:
1. Developer pushes application code to GitHub.
2. GitHub Actions runs checks, builds a container image, and pushes it to a registry.
3. CI updates the image reference in a GitOps repository (for example, a Helm values file).
4. Argo CD detects the Git change and reconciles the target Kubernetes environment to the declared desired state.
5. Dev, UAT, and Production use separate promotion and approval controls.

GitHub Actions builds and publishes artifacts; Argo CD reconciles Kubernetes state. A successful sync alone does not prove application correctness.

## 2. KMH mapping
- Operating Intelligence Architecture: release policy, approval rules, evidence requirements, and rollback criteria.
- Production services / agents: containerized workloads, only if/when a Kubernetes runtime is adopted.
- GitHub Actions: tests, build, image publishing, and controlled GitOps change proposal/update.
- Container registry: immutable/versioned images.
- GitOps repository: environment-specific desired state and deployment history.
- Argo CD: reconciliation and drift detection.
- QA / Immune System: health checks, smoke tests, release verification, and rollback decision.

This is a proposed future architecture for KMH; it does not assert that KMH currently has a working Kubernetes cluster or Argo CD deployment.

## 3. Recommended safe release flow
- Build on a controlled branch and run tests before publishing.
- Tag images with a unique version (commit SHA or release version); prefer digest pinning for stronger immutability. Do not rely on the `latest` tag alone.
- Promote the same tested artifact across environments where practical.
- Require explicit approval for Production.
- Keep secrets out of Git; use least-privilege credentials and repository/environment protections.
- Verify rollout health and application-level behavior, not just Argo CD sync status.
- Keep a known-good image reference and documented rollback procedure.

## 4. Argo CD Image Updater note
Argo CD Image Updater can automate image discovery and updates under configured policies. Its write-back method, allowed tags, and environment promotion rules must be configured deliberately. It should not silently promote untested images into Production.

## 5. Build → Connect → Run → Verify
### Build
Draft the repository layout, workflow YAML, Helm values example, and environment promotion rules. Do not deploy until prerequisites are known.
### Connect
Check repository permissions, registry choice, Kubernetes access, Argo CD availability, and secrets strategy. Record each as confirmed / missing / unverified.
### Run
Use a non-production sandbox and a minimal sample service. Run CI, publish a versioned image, update GitOps state, and let Argo CD reconcile.
### Verify
Capture workflow run, commit SHA, image digest, Argo CD sync/health status, rollout result, and smoke-test output. If not run, mark Pending / Not Run, never PASS.

## 6. Acceptance checklist
- [ ] Application tests pass in CI.
- [ ] Image is published with a traceable immutable reference.
- [ ] GitOps change is reviewable and environment-scoped.
- [ ] Production change requires an approval gate.
- [ ] Argo CD reconciles the expected commit and image.
- [ ] Kubernetes rollout and application smoke test pass.
- [ ] Rollback path is documented and tested in non-production.
- [ ] Evidence links and commit SHAs are recorded.

## 7. Current limitations / next action
The available KMH context confirms separate Notion and GitHub connections, but does not establish a Kubernetes cluster, registry, Argo CD instance, or automatic Notion↔GitHub synchronization. The next real-world step is a readiness inventory and a draft-only implementation plan; actual deployment remains blocked until environment access is confirmed.

## References
- KMH Research Protocol — Notion ↔ GitHub Connection v1.0: https://app.notion.com/p/3fcfd51bf575817881aae80f0619d056
- KMH OIA repository: https://github.com/thuyainminnyo-hub/kmh-oia
