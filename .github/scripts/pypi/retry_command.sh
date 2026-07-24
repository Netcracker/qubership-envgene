#!/usr/bin/env bash

# Shared retry helper for GitHub Actions workflows.
#
# Usage (source in a step, then call retry_command):
#   source ".github/scripts/pypi/retry_command.sh"
#   retry_command MAX_ATTEMPTS DELAY_SECONDS RETRY_ON MESSAGE -- command [args...]
#
# RETRY_ON:
#   - "any" to retry on any non-zero exit code
#   - space-separated exit codes (for example "2" or "2 3")

retry_command() {
  local max_attempts="${1:?max_attempts required}"
  local delay_seconds="${2:?delay_seconds required}"
  local retry_on="${3:?retry_on required}"
  local message="${4:?message required}"
  shift 4

  if [[ "${1:-}" == "--" ]]; then
    shift
  fi

  if [[ "$#" -eq 0 ]]; then
    echo "ERROR: retry_command requires a command after '--'." >&2
    return 2
  fi

  local attempt=1
  local exit_code=0

  while true; do
    set +e
    "$@"
    exit_code=$?
    set -e

    if [[ "${exit_code}" -eq 0 ]]; then
      return 0
    fi

    local should_retry=false
    if [[ "${retry_on}" == "any" ]]; then
      should_retry=true
    else
      local code
      for code in ${retry_on}; do
        if [[ "${exit_code}" -eq "${code}" ]]; then
          should_retry=true
          break
        fi
      done
    fi

    if [[ "${should_retry}" == "true" && "${attempt}" -lt "${max_attempts}" ]]; then
      echo "${message} (attempt ${attempt}/${max_attempts}, exit ${exit_code}), retrying in ${delay_seconds}s..."
      attempt=$((attempt + 1))
      sleep "${delay_seconds}"
      continue
    fi

    return "${exit_code}"
  done
}
