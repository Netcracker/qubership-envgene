#!/bin/bash
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "Usage: sparse_checkout.sh <path> [<path> ...]" >&2
  exit 1
fi

cd "${CI_PROJECT_DIR}"

git config --global init.defaultBranch main
git init .
git remote add origin "${CI_REPOSITORY_URL}"
git -c protocol.version=2 fetch --depth=1 origin \
  "+refs/heads/${CI_COMMIT_REF_NAME}:refs/remotes/origin/${CI_COMMIT_REF_NAME}"
git checkout --force "${CI_COMMIT_SHA}"
git sparse-checkout init --cone
git sparse-checkout set "$@"
git read-tree -mu HEAD
