# P1 — Craft Anything Source Intake & Phone-First Feasibility

**Status:** SOURCE INSPECTION COMPLETE / CLOUD BUILD NOT RUN / EXECUTION HOLD  
**Reviewed:** 2026-11-02  
**Upstream:** https://github.com/storytold/craft-anything  
**Reviewed upstream main commit:** `5185f36ab0c38e6446f40fe537763b8c3f8b260b`  
**KMH OIA pilot branch:** `docs/craft-anything-phone-first-pilot`

## 1. Source provenance and license

Files inspected directly from upstream GitHub:

| File | Observed evidence |
|---|---|
| `README.md` | Rust engine, desktop app, CLI, MCP, Clean room / Deep modes, workflow and alpha status |
| `Cargo.toml` | Workspace version 0.2.0; edition 2024; Rust minimum 1.97; dual license declaration |
| `LICENSE-MIT` | MIT license text present |
| `LICENSE-APACHE` | Apache 2.0 license text present |
| `docs/STATUS.md` | Current feature verification and limitations |
| `docs/ROADMAP.md` | Maintainer roadmap and open dependencies |
| `docs/claude-code.md` | Builder integration requires local unmodified Claude Code and user sign-in |
| `docs/tool-status.md` | Toolset audit; Android device-backed tools are largely unverified without a device |
| `packaging/web/README.md` | Browser viewer is static WASM; file inspection stays in browser; external engines, running programs and AI backends require desktop app |

The workspace declares `MIT OR Apache-2.0`. Preserve both license files, notices and third-party attribution when redistributing. Repository README states brand assets/trademarks are separately controlled; do not reuse Craft Anything or ArtCraft logos/wordmarks in KMH OIA materials.

## 2. Functional architecture observed

- Study → Build → Check → Refine workflow.
- Desktop app, CLI and MCP server use a shared Rust engine.
- Clean room mode restricts inspection to visitor-visible evidence and user-supplied captures.
- Deep mode can inspect code/files of authorized targets.
- Results carry evidence, confidence, coverage and limitations.
- CLI/MCP can expose the engine to agents, subject to permissions and approval prompts.

## 3. Phone-first compatibility assessment

| Capability | Z Fold7 / Android browser | Assessment |
|---|---|---|
| Read upstream docs, inspect issues and source | Yes | Suitable |
| Edit KMH pilot documentation through GitHub | Yes | Suitable |
| Use hosted Codespaces terminal | Browser workflow, subject to account access | Candidate; not tested |
| Run the native egui desktop app on Android | No supported Android build identified | Not supported by evidence |
| Use upstream browser WASM viewer | Browser-based static viewer | Limited; not the full desktop/CLI workflow |
| Run native Android device inspection tools | Requires device bridge / adb and supported host setup | Not verified |
| Full AI build loop | Requires a local signed-in Claude Code executable in upstream's documented integration | Blocked under free-only constraint until a genuinely free, supported builder is verified |

The WASM viewer is not a browser-hosted replacement for the complete desktop application. Upstream documentation says the viewer analyzes files locally in the browser; running programs, external engines and AI backends require the desktop app.

## 4. Free-only constraint — critical finding

The documented default builder is the user's own unmodified Claude Code installation and sign-in. The upstream integration documentation states usage is billed under the user's own Anthropic agreement. Therefore **do not use Claude Code as the assumed free builder**.

API-key backends are documented for questions and analysis, but upstream says API-key building still needs a file-writing tool loop in its own agent and is not yet verified as a live build path.

Decision:
- P1 may proceed with documentation, source review, static inspection and non-billed local/hosted CI checks.
- Do not start an AI rebuild, invoke paid model usage, create a paid resource, or add a billing method.
- P2/P3 remain HOLD until a no-cost, policy-compliant builder path is proven and approved.
- Codespaces must be used only within included quota and only after spending protection is confirmed. If quota or billing guardrails are unclear, stop.

## 5. Responsible-use boundary

Only study targets owned by KMH or explicitly authorized by the owner. Begin in Clean room mode. Do not bypass login, DRM, anti-cheat, paywalls or technical access controls. Do not copy source code, logos, photos, text or protected assets into a rebuild without rights. Use synthetic data for the pilot.

## 6. Evidence and verification still required

- Pin the exact upstream source commit and release tag for each build.
- Confirm current Codespaces allowance and spending controls in the account before starting any Codespace.
- In a Codespace, capture `rustc --version`, `cargo --version`, `cargo metadata --no-deps`, source SHA, command output and exit codes.
- Run only documented, bounded, non-paid checks first.
- Confirm whether the upstream workspace can compile its CLI on a 2-core Codespace within quota; do not infer success from source inspection.
- Keep CI test results separate from real Android-device execution evidence.

## 7. Gate decision

| Gate | Decision |
|---|---|
| Source provenance reviewed | PASS — commit and source files recorded |
| License text reviewed | PASS — MIT and Apache 2.0 files present |
| Phone-first fit | PARTIAL — control plane feasible; native desktop engine not Android-native |
| Free AI builder available | HOLD — not established |
| Codespaces build | NOT RUN |
| Android native execution | NOT RUN |
| OIA integration | NOT AUTHORIZED |

**P1 source intake: PASS WITH LIMITATIONS.**  
**P2 cloud build: HOLD pending explicit free-tier guardrail check.**  
**P3 AI reconstruction and P4 OIA integration: HOLD.**

No Codespace was created, no Rust build was run, no AI agent was invoked, and no Android native execution is claimed by this report.
