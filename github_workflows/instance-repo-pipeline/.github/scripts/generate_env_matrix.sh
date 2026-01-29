#!/bin/bash

if [ -z "$ENV_NAMES" ]; then
    echo "Error: ENV_NAMES is not set"
    exit 1
fi

env_matrix=$(echo "$ENV_NAMES" | jq -R -s -c 'split(",") | map(split(";")) | flatten | map(split(" ")) | flatten | map(split("\n")) | flatten | map(select(. != "" and . != null)) | map(gsub("^\\s+|\\s+$"; "")) | map(select(. != ""))')

echo "env_matrix=$env_matrix" >>$GITHUB_OUTPUT
echo "Generated matrix: $env_matrix"
