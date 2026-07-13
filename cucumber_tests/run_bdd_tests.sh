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

# 1. Build and start the cucumber container
echo "[1/4] Building and starting cucumber container..."
docker compose -f devtools/docker-compose.yml up -d --build cucumber

cleanup() {
    echo "[4/4] Tearing down Docker Compose environment..."
    docker compose -f devtools/docker-compose.yml down --rmi local
}
trap cleanup EXIT

# 2. Install Python packages from mounted source repo
echo "[2/4] Installing envgene Python packages from source repo..."
docker compose -f devtools/docker-compose.yml exec -T cucumber \
    bash -c "chmod +x /workspace/devtools/cucumber/up.sh && /workspace/devtools/cucumber/up.sh"

# 3. Run pytest
echo "[3/4] Executing BDD tests..."
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
