#!/bin/bash
set -euxo pipefail

cd "${CI_PROJECT_DIR}"

export FULL_ENV_NAME="sdp-dev/env-1"
export BG_STATE=""

rm -f junit.xml junit_*.xml

cd python/envgene/envgenehelper
pytest --capture=no -W ignore::DeprecationWarning --junitxml=../../../junit.xml
cd ../../..
mv junit.xml junit_envgenehelper.xml

cd build_pipegene/scripts
pytest --capture=no -W ignore::DeprecationWarning --junitxml=../../junit.xml
cd ../..
mv junit.xml junit_pipegene.xml

cd python/artifact-searcher/artifact_searcher
pytest --capture=no -W ignore::DeprecationWarning --junitxml=../../../junit.xml
cd ../../..
mv junit.xml junit_artifact_searcher.xml

cd scripts/bg_manage
pytest --capture=no -W ignore::DeprecationWarning --junitxml=../../junit.xml
cd ../..
mv junit.xml junit_bg_manage.xml

cd scripts/build_env
pytest --capture=no -W ignore::DeprecationWarning --junitxml=../../junit.xml
cd ../..
mv junit.xml junit_build_env.xml

cd creds_rotation/scripts
pytest --capture=no -W ignore::DeprecationWarning --junitxml=../../junit.xml
cd ../..
mv junit.xml junit_cred_rotation.xml

cd build_effective_set_generator/scripts
pytest --capture=no -W ignore::DeprecationWarning --junitxml=../../junit.xml
cd ../..
mv junit.xml junit_sbom_retention.xml

junitparser merge junit_*.xml junit.xml
