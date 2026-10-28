#!/usr/bin/env bash
# Capture a reproducible local verification record for the synthetic TGiTrailRun pilot.
# This script does not install packages, access network services, or deploy anything.
set -u

if ! repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  printf 'ERROR: run this script from inside a Git checkout.\n' >&2
  exit 2
fi
cd "$repo_root" || exit 2

if [[ $# -ne 1 || ! "$1" =~ ^[0-9a-fA-F]{40}$ ]]; then
  printf 'Usage: bash scripts/capture_tgi_trailrun_local_verification.sh <expected-pr-head-sha>\n' >&2
  printf 'Use the current PR #137 branch-head SHA shown on GitHub.\n' >&2
  exit 2
fi

expected_sha="$1"
actual_sha="$(git rev-parse HEAD 2>/dev/null)" || exit 2
branch_name="$(git branch --show-current 2>/dev/null || true)"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
log_file="tgi-trailrun-local-verification-${timestamp}.log"
if [[ -e "$log_file" ]]; then
  printf 'ERROR: refusing to overwrite existing log: %s\n' "$log_file" >&2
  exit 2
fi
umask 077
if ! : > "$log_file"; then
  printf 'ERROR: cannot create log file: %s\n' "$log_file" >&2
  exit 2
fi

overall_status=0
log_write_failed=0
set -o pipefail

emit() {
  if ! printf '%s\n' "$*" | tee -a "$log_file"; then
    printf 'ERROR: failed to write verification log; evidence may be incomplete.\n' >&2
    overall_status=1
    log_write_failed=1
  fi
}

run_check() {
  local label="$1"
  shift
  local -a pipeline_status
  emit ""
  emit "===== ${label} ====="
  "$@" 2>&1 | tee -a "$log_file"
  pipeline_status=("${PIPESTATUS[@]}")
  local command_status="${pipeline_status[0]:-1}"
  local tee_status="${pipeline_status[1]:-1}"
  emit "command_exit_code=${command_status}"
  emit "log_write_exit_code=${tee_status}"
  if [[ "$command_status" -ne 0 || "$tee_status" -ne 0 ]]; then
    overall_status=1
  fi
  if [[ "$tee_status" -ne 0 ]]; then
    log_write_failed=1
    printf 'ERROR: tee failed while recording check output.\n' >&2
  fi
}

emit "KMH OIA x TGiTrailRun local synthetic verification"
emit "timestamp_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
emit "repository_root=$repo_root"
emit "branch=${branch_name:-DETACHED_HEAD}"
emit "expected_pr_head_sha=$expected_sha"
emit "local_checkout_sha=$actual_sha"
emit "python_path=$(command -v python 2>/dev/null || printf 'NOT_FOUND')"

if [[ "$actual_sha" != "$expected_sha" ]]; then
  emit "head_sha_match=FAIL"
  overall_status=1
else
  emit "head_sha_match=PASS"
fi

if [[ -z "$(git status --porcelain 2>/dev/null)" ]]; then
  emit "working_tree_clean=PASS"
else
  emit "working_tree_clean=FAIL"
  emit "working_tree_status:"
  git status --short 2>&1 | tee -a "$log_file"
  overall_status=1
fi

run_check "Python version" python --version
run_check "Required JSON Schema dependency" python -m pip show jsonschema
run_check "Full repository unit test suite" python -m unittest discover -s tests -v
run_check "Compile source, tests, and scripts" python -m compileall -q src tests scripts
run_check "Repository deployment preflight (validation only)" python scripts/deployment_preflight.py
run_check "Git whitespace/conflict-marker check" git diff --check

emit ""
if [[ "$overall_status" -eq 0 ]]; then
  emit "OVERALL_RESULT=PASS"
  emit "This record is local engineering evidence only; it is not production approval."
else
  emit "OVERALL_RESULT=FAIL"
  emit "Review failed checks and rerun on a clean checkout of the intended SHA."
fi
emit "log_file=$log_file"
emit "Release decision remains HOLD unless all security and owner approval gates are independently closed."
exit "$overall_status"
