# KMH Argo CD GitOps — Android-Only Readiness Plan

**Date:** 2026-10-18  
**Status:** PREPARATION ONLY — no Kubernetes cluster or Argo CD access available; no deployment executed.  
**Device constraint:** Android phone only.  
**Parent case study:** `docs/research/case-studies/argocd-gitops-image-update-automation.md`

## Decision
Do not attempt a real Argo CD deployment yet. First prepare and validate the workflow design, then choose a sandbox/runtime that can actually be operated from the phone. GitHub/Notion access alone does not provide a Kubernetes cluster, registry, or Argo CD instance.

## Phase 0 — Readiness inventory
- [x] Confirmed by user: Android phone only.
- [x] Confirmed by user: no Kubernetes cluster or Argo CD currently available.
- [x] Existing KMH GitHub repository access is available; case-study artifact was committed.
- [ ] Decide whether a hosted Kubernetes sandbox is acceptable, including cost and account requirements.
- [ ] Confirm a container registry choice and free-tier/cost limits before creating resources.
- [ ] Confirm whether the user can access GitHub Actions workflow pages in mobile browser.
- [ ] Never store tokens, passwords, or cloud credentials in this checklist or a public repository.

## Phase 1 — Prepare without infrastructure
1. Draft a minimal sample service and Dockerfile in a dedicated branch or lab repository.
2. Draft a GitHub Actions CI workflow that runs tests and builds the image; initially do not publish or deploy.
3. Draft a GitOps Helm values example using an explicit version/digest placeholder.
4. Draft Dev/UAT/Production promotion rules. Production must require manual approval.
5. Review YAML and workflow permissions before running anything.

## Phase 2 — Connect only after choosing a sandbox
1. Verify account, cluster version, registry, Argo CD endpoint, and permissions.
2. Create only the minimum non-production resources; review estimated charges first.
3. Store credentials in GitHub Actions secrets or an appropriate secret manager, using least privilege.
4. Configure Argo CD to watch the dedicated GitOps path/repository.

## Phase 3 — Run and verify
- CI test result and workflow run URL.
- Image tag and immutable digest.
- GitOps commit SHA and diff.
- Argo CD sync and health state.
- Kubernetes rollout status and application smoke-test output.
- Rollback procedure and result in non-production.

If an action has not been run, its state remains **Pending / Not Run**. A successful sync alone is not sufficient proof that the application works.

## Mobile-friendly next action
Use the GitHub mobile browser/app to open the existing `kmh-oia` repository and inspect the case-study Markdown file. No install or cloud resource creation is needed for this review. Next, decide whether to use a hosted sandbox; do not create billable infrastructure until cost and access are clear.

## Evidence links
- Case study: https://github.com/thuyainminnyo-hub/kmh-oia/blob/main/docs/research/case-studies/argocd-gitops-image-update-automation.md
- Repository: https://github.com/thuyainminnyo-hub/kmh-oia
- Notion case-study record: https://app.notion.com/p/3fdfd51bf57581a7916dc11ab083489a?pvs=204
