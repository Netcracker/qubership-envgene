#!/bin/bash
set -e

SCRIPTPATH="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd -P)"

install_and_clean() {
    local path="$1"
    local name="$2"
    local base_path="${3:-$SCRIPTPATH}"  # optional third argument to function

    echo "Installing $base_path/$path"
    if [ "$IS_LOCAL_DEV_TEST_ENVGENE" = "true" ]; then
      echo "Installing in local test mode"
      uv pip install --editable "$base_path/$path"
    else
      uv pip install --system "$base_path/$path"
    fi

    echo "Removing build trash..."
    rm -rf "$base_path/$path/build" "$base_path/$path/$name.egg-info"
}

pip install uv # pip replacer, makes this script run ~2.8x faster
install_and_clean "envgene" "envgenehelper"
install_and_clean "jschon-sort" "jschon_sort"
install_and_clean "integration" "integration_loader"

