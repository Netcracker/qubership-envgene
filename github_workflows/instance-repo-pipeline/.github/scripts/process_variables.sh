#!/bin/bash
# process_variables.sh — export workflow_dispatch inputs and GH_ADDITIONAL_PARAMS to GITHUB_ENV.
#
# Required env:
#   WORKFLOW_INPUTS  — JSON object from ${{ toJSON(github.event.inputs) }}
#   GITHUB_ENV       — set automatically by GitHub Actions
#
# New workflow inputs: add only under on.workflow_dispatch.inputs — this script picks them up.

set -euo pipefail

if [[ -z "${GITHUB_ENV:-}" ]]; then
  echo "::error::GITHUB_ENV is not set"
  exit 1
fi

if [[ -z "${WORKFLOW_INPUTS:-}" || "$WORKFLOW_INPUTS" == "null" ]]; then
  echo "::error::WORKFLOW_INPUTS is empty (expected toJSON(github.event.inputs))"
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "::error::jq is required"
  exit 1
fi

echo "Exporting workflow_dispatch inputs to GITHUB_ENV..."
echo "$WORKFLOW_INPUTS" | jq -r '
  to_entries[]
  | select(.value != null)
  | "\(.key)=\(.value|tostring)"
' >> "$GITHUB_ENV"

ENV_NAMES="$(echo "$WORKFLOW_INPUTS" | jq -r '.ENV_NAMES // empty')"
if [[ -z "$ENV_NAMES" ]]; then
  echo "::error::ENV_NAMES is required"
  exit 1
fi
if [[ ! "$ENV_NAMES" =~ ^[A-Za-z0-9_./,\;[:space:]-]+$ ]]; then
  echo "::error::ENV_NAMES contains unsupported characters: $ENV_NAMES"
  exit 1
fi
echo "ENV_NAMES validated: $ENV_NAMES"

echo "Processing GH_ADDITIONAL_PARAMS..."
ADDITIONAL_VARS="$(echo "$WORKFLOW_INPUTS" | jq -r '.GH_ADDITIONAL_PARAMS // empty')"

if [[ -z "$ADDITIONAL_VARS" ]]; then
  echo "GH_ADDITIONAL_PARAMS is empty, skipping..."
else
  echo "Raw GH_ADDITIONAL_PARAMS: $ADDITIONAL_VARS"
  IFS=',' read -ra VAR_PAIRS <<<"$ADDITIONAL_VARS"

  for pair in "${VAR_PAIRS[@]}"; do
    pair_clean="$(echo "$pair" | xargs)"
    [[ -z "$pair_clean" ]] && continue

    IFS='=' read -r var_name var_value <<<"$pair_clean"
    var_name_clean="$(echo "$var_name" | xargs)"

    if [[ -n "$var_name_clean" && -n "$var_value" ]]; then
      echo "Found variable: $var_name_clean=$var_value"
      echo "$var_name_clean=$var_value" >>"$GITHUB_ENV"
      echo "✅ $var_name_clean written to GITHUB_ENV"
    else
      echo "⚠️  Invalid variable assignment: $pair_clean"
    fi
  done
  echo "Finished processing GH_ADDITIONAL_PARAMS"
fi

PACKAGE_NAME="generate_pipeline_$(date -u +%Y%m%d_%H%M%S)"
echo "PACKAGE_NAME=$PACKAGE_NAME" >> "$GITHUB_ENV"
echo "PACKAGE_NAME=$PACKAGE_NAME"
