# Phase 02.1 — Graphify Source & Version Intake

**Review date:** 2026-11-02  
**Candidate:** Graphify `v0.9.100`  
**Package:** PyPI `graphifyy` (official package name; CLI command is `graphify`)  
**Decision:** Source candidate verified; installation/indexing still NOT AUTHORIZED and NOT RUN. The release's locked runtime dependencies have not yet passed a separate vulnerability audit.

## 1. Release identity and provenance

- Official source repository: https://github.com/Graphify-Labs/graphify
- Release tag: `v0.9.100`
- Release commit: `f5155badddaa3286c78a51653791131e9e2e4d29`
- PyPI package: https://pypi.org/project/graphifyy/0.9.100/
- Wheel: `graphifyy-0.9.100-py3-none-any.whl`
- Wheel SHA-256: `64c5ed6f2dcc8c28b6a96c87023851c1644c16f55a87f45dbc9127119eb6e769`
- PyPI reports Trusted Publishing provenance linking the wheel to the official GitHub repository, the release commit above, and the upstream `.github/workflows/publish.yml` workflow.
- The release is dated 2026-11-01. This is a new upstream release; re-check release and advisory status immediately before any approved installation.

## 2. License review

The exact v0.9.100 source `pyproject.toml` declares `Apache-2.0`. The tag also includes `LICENSE`, `LICENSE-MIT`, and `NOTICE`. The NOTICE explains that portions contributed before relicensing remain under MIT terms. Preserve all relevant notices and license texts if redistributing source or a modified bundle. This is a technical intake record, not legal advice.

## 3. Dependency and feature review

The base runtime dependency profile includes NetworkX, NumPy, RapidFuzz, PyYAML, conditional TOML support, the Tree-sitter runtime, and a broad set of language grammar packages (including Python, JavaScript/TypeScript, Go, Rust, Java, C/C++, Ruby, C#, Kotlin, Scala, PHP, Swift, Lua, Zig, PowerShell, Elixir, Objective-C, Julia, Verilog, Fortran, Bash, and JSON).

The following are optional extras, not required for the first Python-only fixture:
- PDF and office document extraction.
- Video/audio transcription and media helpers.
- MCP server, database connectors, and hosted graph database integrations.
- OpenAI, Anthropic, Gemini, Bedrock, Ollama and other model-provider SDKs.
- Extra language extractors and visualisation features.

**Pilot dependency decision:** do not install `[all]` or any optional extra. Use the exact release tag's `uv.lock` with `uv sync --locked --no-dev --python 3.12`. This uses the upstream locked resolution and skips the development dependency group and optional extras. No assistant skill, git hook, MCP server, model SDK or global integration is enabled.

A separate runtime dependency audit remains mandatory before installation. The uv lockfile format is specific to uv, so export the exact selected runtime dependency set from the locked source tree and pass the resulting fully pinned requirements file to PyPA's `pip-audit`. Do not claim the lockfile or transitive dependencies are vulnerability-free until this audit produces evidence.

## 4. Security advisory review

Upstream advisory: https://github.com/advisories/GHSA-pcc4-rvhr-2pr8

- Affected range: `graphifyy >=0.7.2,<0.9.70`.
- Patched release: `0.9.70`.
- Candidate: `0.9.100`, outside the affected range.
- The v0.9.100 `graphify/extractors/fortran.py` source was inspected. It strips Fortran C-preprocessor `#include` directives before preprocessing and passes the sanitized source bytes to `cpp` via stdin, rather than passing the original file path.
- This closes the specific absolute/path-traversal include issue described in the advisory. It is not a general security certification of Graphify or its entire dependency tree.

## 5. Important operational distinction

The package install, assistant skill install, graph extraction, and later agent integration are separate operations. The pilot may eventually install only the CLI in an isolated tool environment. Do **not** run `graphify install`, `graphify hook install`, MCP server setup, `--global`, or any model/document/media processing in this phase.

## 6. Exact future procedure — only after explicit owner approval

The commands below are an operator runbook, not an execution record. They have NOT been run.

```bash
set -euo pipefail
WORK="$(mktemp -d)"
GRAPHIFY_REPO="$WORK/graphify-source"
SCAN_ROOT="$WORK/scan"
OUT_ROOT="$WORK/out"
EXPECTED_SOURCE_COMMIT="f5155badddaa3286c78a51653791131e9e2e4d29"

git clone --depth 1 --branch v0.9.100 \
  https://github.com/Graphify-Labs/graphify.git "$GRAPHIFY_REPO"
test "$(git -C "$GRAPHIFY_REPO" rev-parse HEAD)" = "$EXPECTED_SOURCE_COMMIT"

(
  cd "$GRAPHIFY_REPO"
  uv export --locked --no-dev --no-emit-project --format requirements.txt --output-file "$WORK/runtime-requirements.txt"
  uv export --locked --no-dev --no-emit-project --format cyclonedx1.5 --output-file "$WORK/runtime-sbom.json"
  uvx --from pip-audit pip-audit --version > "$WORK/pip-audit-version.txt"
  uvx --from pip-audit pip-audit --strict --no-deps --disable-pip --requirement "$WORK/runtime-requirements.txt" --format json --output "$WORK/dependency-audit.json"
  uv sync --locked --no-dev --python 3.12
)

mkdir -p "$SCAN_ROOT/src" "$OUT_ROOT"
cp -- case-studies/creative-intelligence-design-studio/graphify-sandbox/.graphifyignore "$SCAN_ROOT/"
cp -- case-studies/creative-intelligence-design-studio/graphify-sandbox/src/contract_guard.py "$SCAN_ROOT/src/"
cp -- case-studies/creative-intelligence-design-studio/graphify-sandbox/src/outfit_flow.py "$SCAN_ROOT/src/"

# Freeze the exact three-file synthetic scan snapshot before invoking Graphify.
chmod -R a-w "$SCAN_ROOT"
test "$(find "$SCAN_ROOT" -type f | wc -l | tr -d ' ')" = "3"
find "$SCAN_ROOT" -type f -print0 | sort -z | xargs -0 sha256sum > "$WORK/scan-manifest.sha256"

GRAPHIFY_BACKEND=none "$GRAPHIFY_REPO/.venv/bin/graphify" extract "$SCAN_ROOT" \
  --code-only --no-dedup --out "$OUT_ROOT"

# Review only sanitized evidence. The output is outside the source snapshot.
test -s "$OUT_ROOT/graphify-out/graph.json"
test -s "$OUT_ROOT/graphify-out/GRAPH_REPORT.md"
```

Before installation, require a clean `pip-audit` result for the exported base runtime dependency set; retain the CycloneDX SBOM, requirements export, audit JSON and exact audit-tool version. Do not proceed if known vulnerabilities or incomplete dependency collection are reported. After review, record the source version, lockfile, runner details, source commit, dependency evidence, scan manifest, output graph counts, source references, edge confidence, false connections and reviewer decision. Remove the temporary workspace after exporting sanitized evidence. Do not commit generated `graph.json` or graph reports.

## 7. Intake gates

**Phase 02.1 CI evidence (2026-11-02):** Creative Studio QA run [41420680611](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41420680611) passed source-intake and dependency-audit policy validation, Graphify scope preflight, 20 unit tests and diff check. KMH OIA Tests run [41420680434](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41420680434) passed 462 tests and the performance baseline. KMH OIA Validation run [41420680438](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41420680438) passed repository validation, tests, performance evidence and deployment evidence bundle.

| Gate | Evidence | State |
|---|---|---|
| G0.1 — Official source identity | PyPI package, source tag and provenance commit match | PASS |
| G0.2 — License and dependency review | Apache-2.0 declaration, NOTICE/MIT legacy note, base/optional dependency split and lockfile reviewed | PASS |
| G0.3 — Known advisory review | GHSA range/fix reviewed; v0.9.100 Fortran patch inspected | PASS |
| G0.4 — Locked runtime dependency audit | Exact base requirements exported from v0.9.100 uv.lock; pip-audit report with no known vulnerabilities | PENDING |
| G0.5 — Owner install approval | Explicit approval for isolated tool install and fixture execution | PENDING |
| G1 — Scope guard | Project validator and 14 CI tests | PASS |
| G2 — Isolated Graphify extraction | Actual run from the exact release in disposable workspace | NOT RUN |
| G3 — Source traceability | Sampled EXTRACTED edges verified against the three-file snapshot | NOT RUN |
| G4 — False-connection review | Expected import/call links and unsupported links evaluated | NOT RUN |

**Current decision:** v0.9.100 is a technically reviewed candidate. It is not an approved production dependency. The exact version and wheel checksum are recorded in the machine-readable policy, while `approved_version` remains null, `install_allowed` remains false, and `index_allowed` remains false until explicit owner approval.
