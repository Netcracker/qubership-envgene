#!/bin/bash
set -euxo pipefail

cd "${CI_PROJECT_DIR}"

export PYTHONPATH=${CI_PROJECT_DIR}
export FULL_ENV_NAME="sdp-dev/env-1"
export BG_STATE=""

rm -f junit.xml junit_*.xml

run_pytest_suite() {
  local name="$1"
  local dir="$2"
  (
    cd "${CI_PROJECT_DIR}/${dir}"
    pytest --capture=no -W ignore::DeprecationWarning --junitxml="${CI_PROJECT_DIR}/junit.xml"
  )
  mv "${CI_PROJECT_DIR}/junit.xml" "${CI_PROJECT_DIR}/junit_${name}.xml"
}

run_pytest_suite envgenehelper python/envgene/envgenehelper
run_pytest_suite scripts scripts/tests

junitparser merge junit_*.xml junit.xml
