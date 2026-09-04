#!/usr/bin/env bash
# run_bdd_tests.sh — Local runner for the EIG BDD test suite
# Usage:
#   ./run_bdd_tests.sh                           # run all EIG scenarios
#   ./run_bdd_tests.sh "UC-EINV-ED-1"           # run a specific scenario by name
#   ENVGENE_SOURCE_ROOT=/custom/path ./run_bdd_tests.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCENARIOS="${1:-}"

# Resolve envgene source root: defaults to sibling 'qubership-envgene' directory
SOURCE_ROOT="${ENVGENE_SOURCE_ROOT:-$(realpath "${SCRIPT_DIR}/../../qubership-envgene")}"

echo "================================================="
echo " EIG BDD Test Runner (Docker)"
echo " Source repo: ${SOURCE_ROOT}"
echo "================================================="

# Navigate to project root (parent of cucumber_tests)
cd "${SCRIPT_DIR}/.."

# 1. Rebuild the production base image from the current checkout.
#    The 'cucumber' service (see devtools/cucumber/Dockerfile) is FROM local-envgene-main,
#    which bakes in scripts/ and modules/dpg at build time. Docker will happily reuse a
#    stale local-envgene-main tag left over from a previous run, silently testing old code
#    even though /workspace is volume-mounted with the current checkout - so this rebuild
#    is not optional. This mirrors what the perform_e2e_tests.yml CI workflow does.
echo "[1/5] Rebuilding local-envgene-main base image..."
docker build -t local-envgene-main -f build_envgene/build/Dockerfile .

# 2. Build and start the cucumber container
echo "[2/5] Building and starting cucumber container..."
docker compose -f devtools/docker-compose.yml up -d --build cucumber

cleanup() {
    echo "[5/5] Tearing down Docker Compose environment..."
    docker compose -f devtools/docker-compose.yml down --rmi local
}
trap cleanup EXIT

# 3. Install Python packages from mounted source repo
echo "[3/5] Installing envgene Python packages from source repo..."
docker compose -f devtools/docker-compose.yml exec -T cucumber \
    bash -c "chmod +x /workspace/devtools/cucumber/up.sh && /workspace/devtools/cucumber/up.sh"

# 4. Run pytest
echo "[4/5] Executing BDD tests..."
mkdir -p reports

if [ -n "${SCENARIOS}" ]; then
    PYTEST_CMD="pytest cucumber_tests/step_defs/ -c cucumber_tests/pytest.ini -k '${SCENARIOS}' -v -s --junitxml=reports/eig.xml"
else
    PYTEST_CMD="pytest cucumber_tests/step_defs/ -c cucumber_tests/pytest.ini -v -s --junitxml=reports/eig.xml"
fi

docker compose -f devtools/docker-compose.yml exec -T cucumber \
    bash -c "set -o pipefail; export PYTHONPATH=/workspace:/workspace/scripts:/envgene-src && cd /workspace && mkdir -p reports && ${PYTEST_CMD} | tee bdd_tests.log"

echo ""
echo "Tests complete. Results saved to:"
echo "  - reports/eig.xml  (JUnit XML)"
echo "  - e2e_tests.log    (full stdout)"
