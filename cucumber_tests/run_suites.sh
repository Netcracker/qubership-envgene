#!/usr/bin/env bash
# Runs every pytest-bdd suite under cucumber_tests/step_defs, one pytest process per suite.
#
# Suites are discovered from the filesystem, so a new test_<name>.py runner is picked up by CI
# without editing any workflow. Extra arguments are passed through to pytest, e.g.
#   cucumber_tests/run_suites.sh -k "UC-CC-DP-1"
#
# Deliberately no `set -e`: every suite runs even after one fails, so a single broken suite cannot
# hide the state of the others. The aggregated failure is reported through the exit code.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# In the cucumber container PYTHONPATH is normally unset; scripts/ is not a package and is resolved
# purely through PYTHONPATH (see CLAUDE.md).
export PYTHONPATH="${PYTHONPATH:-${REPO_ROOT}:${REPO_ROOT}/scripts}"

LOG_FILE="e2e_tests.log"
REPORTS_DIR="reports"

mkdir -p "$REPORTS_DIR"
: > "$LOG_FILE"

shopt -s nullglob
runners=(cucumber_tests/step_defs/test_*.py)
shopt -u nullglob

if [ "${#runners[@]}" -eq 0 ]; then
    echo "No pytest-bdd runners found under cucumber_tests/step_defs - nothing was tested" >&2
    exit 1
fi

group_start() {
    if [ -n "${GITHUB_ACTIONS:-}" ]; then echo "::group::$1"; else echo "===== $1 ====="; fi
}

group_end() {
    if [ -n "${GITHUB_ACTIONS:-}" ]; then echo "::endgroup::"; fi
}

report_failure() {
    if [ -n "${GITHUB_ACTIONS:-}" ]; then echo "::error::$1 failed"; else echo "$1 FAILED"; fi
}

echo "Discovered ${#runners[@]} suite(s): ${runners[*]}"

failed=0
for runner in "${runners[@]}"; do
    suite="$(basename "$runner" .py)"
    suite="${suite#test_}"

    group_start "$suite"
    if pytest "$runner" \
        -c cucumber_tests/pytest.ini \
        -v -s \
        --junitxml="${REPORTS_DIR}/${suite}.xml" \
        "$@" | tee -a "$LOG_FILE"; then
        echo "$suite passed"
    else
        report_failure "$suite"
        failed=1
    fi
    group_end
done

exit "$failed"
