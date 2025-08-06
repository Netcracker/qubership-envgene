#!/bin/bash
set -e

SCRIPTPATH="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 && pwd -P)"

install_and_clean() {
    local path="$1"
    local name="$2"

    echo "Installing $SCRIPTPATH/$path"
    pip install "$SCRIPTPATH/$path"

    echo "Removing build trash..."
    rm -rf "$SCRIPTPATH/$path/build" "$SCRIPTPATH/$path/$name.egg-info"
}

install_and_clean "envgene" "envgenehelper"
install_and_clean "jschon-sort" "jschon_sort"
install_and_clean "integration" "integration_loader"
install_and_clean "artifact-searcher" "artifact_searcher"
