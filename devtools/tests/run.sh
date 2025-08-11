#!/bin/bash
set -euxo

cd "$CI_PROJECT_DIR"

# Run tests
# cd python/envgene/envgenehelper
# pytest --capture=no -W ignore::DeprecationWarning --junitxml=../../../junit.xml
# cd ../../..
# mv junit.xml junit_envgenehelper.xml

cd scripts/build_env
pytest --capture=no -W ignore::DeprecationWarning --junitxml=../../junit.xml
cd ../..
mv junit.xml junit_build_env.xml

# Merge results
# python -m junitparser merge junit_build_env.xml junit_envgenehelper.xml junit.xml
