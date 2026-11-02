# Phase 02.1 — Graphify Source & Version Intake

**Review date:** 2026-11-02  
**Candidate:** Graphify `v0.9.100`  
**Package:** PyPI `graphifyy` (official package name; CLI command is `graphify`)  
**Decision:** Source and dependency intake verified. The frozen v0.9.100 base runtime dependency snapshot passed PyPI and OSV audits. Graphify installation/indexing remain NOT AUTHORIZED and NOT RUN.

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

**Pilot dependency decision:** do not install `[all]` or any optional extra. Use the exact release tag's `uv.lock` with uv 0.13.6 and `uv sync --frozen --no-dev --python 3.12`. The upstream v0.9.100 CI explicitly uses `--frozen` to consume the committed lock without re-resolving or rewriting it. Pin the exact `uv.lock` Git blob `1fd2344a28be6b14c4f6f41c4901c70cadc2be0e`. No assistant skill, git hook, MCP server, model SDK or global integration is enabled.

A separate runtime dependency audit remains mandatory before installation. The uv lockfile format is specific to uv, so export the exact selected runtime dependency set from the frozen source snapshot and pass the resulting fully pinned requirements file to PyPA's `pip-audit`. The audit tool is pinned to `pip-audit==2.10.1` (the latest listed PyPI release at this review). Run both the PyPI and OSV vulnerability services. The tool is invoked with `--strict --require-hashes --disable-pip`: `--strict` fails when dependency collection is incomplete, and `--require-hashes` checks that every pinned requirement includes a hash. This is preferred to `--no-deps` when the exported requirements file contains hashes. Do not generalize the clean result to optional extras, development dependencies, or a fresh PyPI resolver graph. The completed audit covers only the exact upstream frozen base-runtime snapshot.

**Lockfile compatibility note:** A first `uv export --frozen` check failed because uv determined that the release tag's `uv.lock` needed updating against its `pyproject.toml`. Upstream v0.9.100 CI deliberately uses `uv sync --frozen` and `uv run --frozen` to consume the committed lock without re-resolving it. The audit therefore mirrors the upstream frozen lock policy, pins uv 0.13.6 and verifies the exact lock blob SHA. This audits the dependency snapshot upstream CI actually consumes; it does not assert that the published PyPI installation resolver will select the same graph if package metadata is independently re-resolved.

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

The dependency-only audit is automated by [graphify-dependency-audit.yml](../../../../.github/workflows/graphify-dependency-audit.yml) on relevant policy/workflow changes. It exports the exact frozen base requirements and CycloneDX SBOM, runs the pinned hash-enforced audit tool against PyPI and OSV, and uploads evidence. It does not install or execute Graphify. The commands below remain a manual operator runbook for the later, separately approved isolated extraction; they have NOT been run.

```bash
set -euo pipefail
KMH_PROJECT_ROOT="$(pwd)"
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
  test "$(git rev-parse v0.9.100:uv.lock)" = "1fd2344a28be6b14c4f6f41c4901c70cadc2be0e"
  uv --version
  uv export --frozen --no-dev --no-emit-project --format requirements.txt --output-file "$WORK/runtime-requirements.txt"
  uv export --frozen --no-dev --no-emit-project --format cyclonedx1.5 --output-file "$WORK/runtime-sbom.json"
  uvx --from "pip-audit==2.10.1" pip-audit --version > "$WORK/pip-audit-version.txt"
  set +e
  uvx --from "pip-audit==2.10.1" pip-audit --strict --require-hashes --disable-pip --requirement "$WORK/runtime-requirements.txt" --format json --output "$WORK/pip-audit-pypi.json"
  PYPI_AUDIT_STATUS=$?
  uvx --from "pip-audit==2.10.1" pip-audit --vulnerability-service osv --strict --require-hashes --disable-pip --requirement "$WORK/runtime-requirements.txt" --format json --output "$WORK/pip-audit-osv.json"
  OSV_AUDIT_STATUS=$?
  set -e
  test "$PYPI_AUDIT_STATUS" -eq 0
  test "$OSV_AUDIT_STATUS" -eq 0
  uv sync --frozen --no-dev --python 3.12
)

mkdir -p "$SCAN_ROOT/src" "$OUT_ROOT"
cp -- "$KMH_PROJECT_ROOT/case-studies/creative-intelligence-design-studio/graphify-sandbox/.graphifyignore" "$SCAN_ROOT/"
cp -- "$KMH_PROJECT_ROOT/case-studies/creative-intelligence-design-studio/graphify-sandbox/src/contract_guard.py" "$SCAN_ROOT/src/"
cp -- "$KMH_PROJECT_ROOT/case-studies/creative-intelligence-design-studio/graphify-sandbox/src/outfit_flow.py" "$SCAN_ROOT/src/"

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

Before installation, require clean PyPI and OSV `pip-audit` 2.10.1 results for the exported base runtime dependency set; retain the CycloneDX SBOM, requirements export, both audit JSON reports and exact audit-tool version. Do not proceed if known vulnerabilities or incomplete dependency collection are reported. `--strict` is supported and deliberately included to fail on dependency-collection errors; `--require-hashes` validates the hash-bearing pinned requirements, and `--disable-pip` prevents a second resolver pass. After review, record the source version, lockfile, runner details, source commit, dependency evidence, scan manifest, output graph counts, source references, edge confidence, false connections and reviewer decision. Remove the temporary workspace after exporting sanitized evidence. Do not commit generated `graph.json` or graph reports.

## 7. Intake gates

**Completed dependency audit (2026-11-02):** Run [41422855820](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41422855820) verified source commit `f5155badddaa3286c78a51653791131e9e2e4d29`, exact `uv.lock` blob `1fd2344a28be6b14c4f6f41c4901c70cadc2be0e`, uv 0.13.6, and pip-audit 2.10.1. Frozen requirements and CycloneDX SBOM exports passed. Hash-enforced `--strict --require-hashes --disable-pip` audits returned exit code 0 for both PyPI and OSV; both logs reported no known vulnerabilities. PyPI service verified requirement hashes; OSV confirmed hash presence and returned no known vulnerabilities. Evidence artifact [13129673852](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41422855820/artifacts/13129673852) was uploaded successfully.

The automated dependency-audit workflow is a read-only source-metadata and vulnerability-check job. Its only package tool installation is the isolated, version-pinned `pip-audit==2.10.1` utility; the Graphify CLI itself is not installed or executed by this workflow.


**Phase 02.1 CI evidence (2026-11-02):** Creative Studio QA run [41420680611](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41420680611) passed source-intake and dependency-audit policy validation, Graphify scope preflight, 20 unit tests and diff check. KMH OIA Tests run [41420680434](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41420680434) passed 462 tests and the performance baseline. KMH OIA Validation run [41420680438](https://github.com/thuyainminnyo-hub/kmh-oia/actions/runs/41420680438) passed repository validation, tests, performance evidence and deployment evidence bundle.

| Gate | Evidence | State |
|---|---|---|
| G0.1 — Official source identity | PyPI package, source tag and provenance commit match | PASS |
| G0.2 — License and dependency review | Apache-2.0 declaration, NOTICE/MIT legacy note, base/optional dependency split and lockfile reviewed | PASS |
| G0.3 — Known advisory review | GHSA range/fix reviewed; v0.9.100 Fortran patch inspected | PASS |
| G0.4 — Frozen runtime dependency audit | Exact frozen lock snapshot; hash-enforced PyPI and OSV reports; retained evidence artifact | PASS — run 41422855820, artifact 13129673852 |
| G0.5 — Owner install approval | Explicit approval for isolated tool install and fixture execution | PENDING |
| G1 — Scope guard | Project validator and 14 CI tests | PASS |
| G2 — Isolated Graphify extraction | Actual run from the exact release in disposable workspace | NOT RUN |
| G3 — Source traceability | Sampled EXTRACTED edges verified against the three-file snapshot | NOT RUN |
| G4 — False-connection review | Expected import/call links and unsupported links evaluated | NOT RUN |

**Current decision:** v0.9.100 is a technically reviewed candidate. It is not an approved production dependency. The exact version and wheel checksum are recorded in the machine-readable policy, while `approved_version` remains null, `install_allowed` remains false, and `index_allowed` remains false until explicit owner approval.
