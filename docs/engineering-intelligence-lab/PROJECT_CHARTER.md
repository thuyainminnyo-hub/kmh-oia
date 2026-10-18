# KMH Engineering Intelligence Lab

- **Parent system:** KMH AI Production Studio
- **Scope:** All engineering domains
- **Purpose:** Turn trusted engineering sources into reusable knowledge, small reproducible experiments, and verified implementation guidance for KMH.
- **Operating loop:** Build → Connect → Run → Verify
- **Current execution constraint:** Android phone-first; no Kubernetes cluster or cloud deployment is assumed to exist.
- **Status:** Charter and source index recorded; live lab execution not yet verified.

## Relationship to existing KMH projects
This is a new cross-domain project identity, not a replacement for existing projects.
- Keep **KMH DevOps Automation Lab** as the focused DevOps/GitOps workstream.
- Keep **Engineering Intelligence Library — Harry Yan 2025 Article Index** as the source register for the 66 supplied articles.
- Keep **KMH OIA** (repository `thuyainminnyo-hub/kmh-oia`) as the existing GitHub repository; do not create a duplicate repository solely for naming.
- Do not rename, delete, or overwrite existing Notion pages, repositories, or files without explicit approval.

## Domain map
1. Software architecture and distributed systems
2. DevOps, cloud native, CI/CD and GitOps
3. Databases and data engineering
4. Observability, reliability and incident response
5. Security engineering
6. Software engineering, APIs and developer workflow
7. Performance and scalability
8. Engineering practice, learning and human factors
9. AI engineering and automation

## Build → Connect → Run → Verify
### Build
Maintain source registers, architecture notes, decision records, run cards, and reproducible test plans.

### Connect
Link each learning item to a relevant existing KMH project/component. Keep Notion and GitHub records traceable; do not claim bidirectional synchronization until tested.

### Run
Start with a low-risk, phone-friendly test using existing tools. Check permissions, cost, data sensitivity, and rollback before any external deployment.

### Verify
Record the expected result, actual result, evidence, status, limitations, and next action. Use **PASS** only when actual evidence supports it; otherwise use **NOT RUN**, **BLOCKED**, or **NEEDS REVIEW**.

## First execution queue
- [x] Search Notion for overlapping project names and relevant existing pages.
- [x] Search connected GitHub repositories for existing KMH repository.
- [x] Register the 66 user-supplied article links in the Engineering Intelligence Library.
- [x] Create this project charter without renaming or deleting existing records.
- [ ] Read and assess the first source article body.
- [ ] Select one phone-friendly, non-production lab.
- [ ] Run the lab and capture real evidence.
- [ ] Verify outcome and record the result in Notion and GitHub.

## Initial source sequence
1. [Cloud native နဲ့ DevOps](https://harryyan.uk/article59.html)
2. [Container ဆိုတာဘာလဲ](https://harryyan.uk/article62.html)
3. [Docker ရဲ့ anti-pattern တချို့](https://harryyan.uk/article55.html)
4. [CI/CD pipeline ဆိုတာ တကယ်တမ်း ဘာတွေလဲ](https://harryyan.uk/article17.html)
5. [Terraform ဘာလဲ](https://harryyan.uk/article19.html)
6. [Prometheus နဲ့ Monitoring အခြေခံ](https://harryyan.uk/article41.html)

## Evidence integrity
The source index is based on titles and URLs supplied by the user. It is not evidence that all article bodies have been read or independently verified. No production infrastructure has been deployed as part of this charter.
