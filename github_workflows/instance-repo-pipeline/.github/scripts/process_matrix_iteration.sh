#!/bin/bash

ITERATION="${1:-}"

if [ -z "$ITERATION" ]; then
    echo "Error: No matrix environment provided"
    echo "Usage: $0 <environment_name>"
    exit 1
fi

echo "Iteration name: $ITERATION"

# Extract cluster and environment names from matrix format
cluster_name=$(echo "$ITERATION" | cut -d'/' -f1)
environment_name=$(echo "$ITERATION" | cut -d'/' -f2 | xargs)

# Export variables for use in the workflow
echo "export FULL_ENV=\"$ITERATION\""
echo "export FULL_ENV_NAME=\"$ITERATION\""
echo "export ENV_NAMES=\"$ITERATION\""
echo "export CLUSTER_NAME=\"$cluster_name\""
echo "export ENVIRONMENT_NAME=\"$environment_name\""
echo "export ENV_NAME=\"$environment_name\""

# For GitHub Actions, also add to GITHUB_ENV
if [ -n "$GITHUB_ENV" ]; then
    echo "FULL_ENV=$ITERATION" >>"$GITHUB_ENV"
    echo "FULL_ENV_NAME=$ITERATION" >>"$GITHUB_ENV"
    echo "ENV_NAMES=$ITERATION" >>"$GITHUB_ENV"
    echo "CLUSTER_NAME=$cluster_name" >>"$GITHUB_ENV"
    echo "ENVIRONMENT_NAME=$environment_name" >>"$GITHUB_ENV"
    echo "ENV_NAME=$environment_name" >>"$GITHUB_ENV"
    echo "✅ Matrix variables written to GITHUB_ENV"
fi
