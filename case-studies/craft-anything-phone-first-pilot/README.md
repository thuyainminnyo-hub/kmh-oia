# Craft Anything Phone-First Pilot — KMH OIA

**Status:** PLAN RECORDED / EXECUTION NOT YET VERIFIED  
**Pilot mode:** Android phone + tablet, cloud-assisted, free-tier only  
**Primary device:** Samsung Galaxy Z Fold7 (512 GB storage variant; RAM is 12 GB on Samsung's US 512 GB SKU)  
**Repository:** https://github.com/storytold/craft-anything  
**Integration boundary:** isolated case study; no OIA Core changes authorized

## 1. Goal

Evaluate Craft Anything as a specialist Software Study & Rebuild tool that may later connect to KMH OIA through governed interfaces. Do not make Craft Anything the OIA Core, and do not promote it into production based on documentation or mocked CI alone.

The user's available environment is a Samsung Galaxy Z Fold7 and a tablet, with both Wi-Fi and mobile data, and a strict **free services only** budget. Therefore use browser-based development and hosted CI; do not require local Rust, Cargo, desktop installation, Termux, a paid API, or a laptop.

## 2. Device interpretation

The phrase "Ram512G" is recorded as **512 GB device storage**, not 512 GB RAM. Samsung's published US 512 GB Z Fold7 SKU lists 12 GB memory and 512 GB storage. Samsung lists other market/storage configurations too; verify the exact model number in Settings > About phone before relying on regional specifications.

The Z Fold7 is a capable browser/control device. It is not a supported native host for the Craft Anything desktop application merely because it has ample storage. Do not claim the desktop Rust GUI, CLI, local video rendering, or local MCP server runs natively on Android.

## 3. Phone-first operating model

| Work | Device / service | Free-tier guardrail |
|---|---|---|
| Review source, issues, branches, PRs | GitHub mobile app or browser | Public repository access |
| Edit docs and small files | GitHub web editor | Commit only to pilot branch |
| Build/test Rust source | GitHub Codespaces in browser | Personal-account included quota only |
| Repeatable checks | GitHub Actions | Prefer public-repo standard hosted runners; inspect current quota/policy |
| Evidence and decisions | Repository Markdown + CI artifacts | No paid storage or external SaaS |
| Native desktop GUI / local GPU render | Not available on phone-only setup | HOLD until a compatible computer is available |

### Codespaces budget protection

GitHub currently documents an included monthly Codespaces quota for personal accounts. The Free personal-account quota is 15 GB-month storage and 120 core-hours (equivalent to 60 hours on a 2-core machine). Usage beyond included quota can be billed if billing is enabled. For this strict free-only pilot:

1. Use a personal-account Codespace only.
2. Before creating it, open GitHub Settings > Billing and licensing > Budgets and alerts and confirm Codespaces spending is blocked / budget is zero. Do not add a payment method just to continue.
3. Prefer a 2-core machine; stop the Codespace when not actively working and delete it after the pilot if no longer needed.
4. Track remaining compute and storage in the GitHub billing dashboard.
5. If included quota is exhausted, pause until reset; do not switch to paid compute.

Free quotas and availability can change. Re-check GitHub's official billing documentation before each new billing period.

## 4. Pilot phases and gates

### P0 — Scope and source intake (current)

- Keep this work on `docs/craft-anything-phone-first-pilot`.
- Inspect Craft Anything's current README, license files, release tags, supported platforms, build instructions, CLI commands, MCP transport, and documented web/WASM path (if any).
- Record exact source commit SHA and release tag used for every experiment.
- Separate upstream claims from KMH OIA's independently observed evidence.
- Do not copy proprietary assets, source code, branding, or restricted data from a target product.

**Exit evidence:** source URL, commit SHA, release tag, license evidence, platform matrix, dependency/build notes, and dated intake report.

### P1 — Cloud build feasibility

**Source intake completed 2026-11-02:** see [P1 source intake report](docs/p1-source-intake.md). The upstream repository was inspected at commit `5185f36ab0c38e6446f40fe537763b8c3f8b260b`. The project is MIT OR Apache-2.0, requires Rust 1.97, and is early alpha. Its full AI build path depends on a local coding agent; the documented Claude Code path uses the user's own account and is not assumed free. The browser WASM viewer is a limited file analyzer, not a substitute for the desktop/CLI rebuild workflow. **P1 source intake: PASS WITH LIMITATIONS; cloud build and AI rebuild remain HOLD.**



- Create a temporary personal Codespace from the upstream repository or a fork/pilot branch.
- Confirm Rust toolchain version required by the checked-out commit; do not assume a version from a social post.
- Run read-only inspection first: `rustc --version`, `cargo --version`, `cargo metadata --no-deps`.
- Run the repository's documented checks and the smallest supported package build. Capture exact commands, exit codes, commit SHA, and logs.
- Do not assume a desktop GUI can be displayed inside a mobile browser Codespace. A successful CLI compile is not a successful Android GUI run.

**Exit evidence:** build log, toolchain versions, exact source SHA, command transcript, test summary, and limitations.

### P2 — Study workflow feasibility

- Select a website or application that the project owner owns or is explicitly authorized to inspect.
- Start with public UI behavior and user-provided test data. Do not bypass authentication, paywalls, access controls, rate limits, or technical protections.
- Keep raw captures separate from normalized findings.
- Record each finding with evidence pointer, confidence, observation date, and reviewer.
- Keep inferred behavior explicitly labelled INFERRED; never promote it to VERIFIED without direct evidence.

**Exit evidence:** source screenshots/URLs, feature inventory, user-flow map, evidence-to-claim traceability, and rights/authorization note.

### P3 — Agent build and compare

- Build a clean-room implementation from independently written requirements and observed behavior.
- Do not copy original source code, logos, product names, protected visual assets, or distinctive content.
- Compare functionality and user flows, not just screenshots.
- Use synthetic data only.
- Require human approval before any file-system, network, deployment, or external-account action.

**Exit evidence:** generated source commit, test results, comparison report, asset provenance, and approval record.

### P4 — Governed OIA integration review

- Treat Craft Anything as an optional external specialist, not a trusted runtime component.
- Define a narrow adapter contract: input manifest, evidence bundle, proposed build plan, result manifest, and audit reference.
- Validate schema, provenance, permissions, timeouts, and artifact hashes at the OIA boundary.
- Deny by default. No automatic promotion, production deployment, or write access to OIA Core.
- Keep the existing OIA Production Module V1 GPU/video pilot separate. Its local NVIDIA NVENC requirement cannot be satisfied by the Z Fold7; phone-based planning does not count as GPU execution evidence.

**Exit evidence:** threat model, adapter contract, permission tests, audit sample, human approval, and an explicit GO/HOLD decision.

## 5. Evidence record schema

Every experiment should record:

- `experiment_id`
- `date_utc`
- `repository`
- `source_commit_sha`
- `release_tag`
- `device` and `environment`
- `toolchain_versions`
- `commands` and exit codes
- `artifact_paths` and SHA-256 hashes
- `test_results`
- `limitations`
- `reviewer_decision` (PASS / HOLD / FAIL)

Never store API keys, access tokens, passwords, private user data, or secrets in the repository or CI logs.

## 6. Acceptance criteria

| Gate | PASS requires | Current status |
|---|---|---|
| P0 source intake | Commit/tag/license/platform evidence recorded | IN PROGRESS |
| P1 cloud build | Reproducible build/test evidence from Codespaces | NOT RUN |
| P2 study | Authorized target + traceable evidence bundle | NOT RUN |
| P3 reconstruction | Independent implementation + functional comparison | NOT RUN |
| P4 integration | Security review + adapter tests + human approval | NOT AUTHORIZED |

**Release decision: HOLD.** This is a planning and source-intake branch only. No Craft Anything installation, cloud build, Android execution, MCP connection, real video render, or production integration is claimed by this document.

## 7. Next operator action

On the Z Fold7 or tablet:

1. Open https://github.com/thuyainminnyo-hub/kmh-oia/tree/docs/craft-anything-phone-first-pilot
2. Review this pilot plan.
3. Open GitHub Codespaces only after confirming the personal-account spending guardrail.
4. Start P1 with source inspection and toolchain version capture; stop if GitHub asks to enable paid billing.

## Official references

- Craft Anything source: https://github.com/storytold/craft-anything
- KMH OIA repository: https://github.com/thuyainminnyo-hub/kmh-oia
- GitHub Codespaces billing: https://docs.github.com/en/billing/concepts/product-billing/github-codespaces
- GitHub Codespaces usage: https://docs.github.com/en/codespaces/about-codespaces/what-are-codespaces
- Samsung Galaxy Z Fold7 specifications: https://www.samsung.com/us/smartphones/galaxy-z/galaxy-z-fold7-silver-shadow-512gb-sm-f966uzsexaa/
