#!/bin/bash
set -e

SCRIPTPATH="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 && pwd -P)"

install_and_clean() {
    local path="$1"
    local name="$2"

    echo "Installing $SCRIPTPATH/$path"
    if [ "$IS_LOCAL_DEV_TEST_ENVGENE" = "true" ]; then
      uv pip install --system -e "$SCRIPTPATH/$path"
    else
      uv pip install --system "$SCRIPTPATH/$path"
    fi

    echo "Removing build trash..."
    rm -rf "$SCRIPTPATH/$path/build" "$SCRIPTPATH/$path/$name.egg-info"
}

pip install uv # pip replacer, makes this script run ~2.8x faster
install_and_clean "envgene" "envgenehelper"
install_and_clean "jschon-sort" "jschon_sort"
install_and_clean "integration" "integration_loader"
install_and_clean "artifact-searcher" "artifact_searcher"
