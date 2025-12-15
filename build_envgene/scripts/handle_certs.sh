#!/bin/bash
set -euo pipefail

certs_dir="${CI_PROJECT_DIR:-}/configuration/certs"
default_cert="/default_cert.pem"

log() { printf '%s\n' "$*"; }

if [ -z "${CI_PROJECT_DIR:-}" ]; then
  log "Error: CI_PROJECT_DIR is not set"
  exit 1
fi

# If certs_dir doesn't exist or is empty, fall back to default_cert
if [ ! -d "$certs_dir" ] || ! find "$certs_dir" -mindepth 1 -print -quit >/dev/null 2>&1; then
  if [ -f "$default_cert" ]; then
    # shellcheck disable=SC1091
    . /module/scripts/update_ca_cert.sh "$default_cert"
  else
    log "No certificates found and default certificate does not exist: $default_cert"
  fi
else
  # Iterate files safely (handles spaces/newlines)
  while IFS= read -r -d '' cert; do
    # shellcheck disable=SC1091
    . /module/scripts/update_ca_cert.sh "$cert"
  done < <(find "$certs_dir" -mindepth 1 -maxdepth 1 -type f -print0)
fi