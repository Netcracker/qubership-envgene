#!/bin/bash
set -euo pipefail

certs_dir="${CI_PROJECT_DIR:-}/configuration/certs"
default_cert="/default_cert.pem"

ENVGENE_LOG_LEVEL="${ENVGENE_LOG_LEVEL:-INFO}"
ENVGENE_LOG_LEVEL="$(printf '%s' "${ENVGENE_LOG_LEVEL}" | tr '[:lower:]' '[:upper:]')"

log() { printf '%s\n' "$*"; }

function debugPrintCertsFromFile {
    local file="$1"
    local label="$2"
    [[ "${ENVGENE_LOG_LEVEL}" != "DEBUG" ]] && return
    echo "[DEBUG] === ${label} ==="
    if [[ ! -e "$file" ]]; then
        echo "[DEBUG] File does not exist: $file"
        return
    fi
    local cert_num=0
    local block=""
    while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line%$'\r'}"
        if [[ "$line" == "-----BEGIN CERTIFICATE-----" ]]; then
            block="$line"
            continue
        fi
        if [[ -n "$block" ]]; then
            block+=$'\n'"$line"
            if [[ "$line" == "-----END CERTIFICATE-----" ]]; then
                cert_num=$((cert_num + 1))
                echo "[DEBUG] --- Certificate #${cert_num} in ${file} ---"
                printf "%s\n" "$block" | openssl x509 -noout -subject -issuer -dates 2>/dev/null || echo "[DEBUG] (openssl could not decode this block)"
                block=""
            fi
        fi
    done < "$file"
    if [[ $cert_num -eq 0 ]]; then
        echo "[DEBUG] No PEM certificate blocks found in ${file}"
    else
        echo "[DEBUG] Total: ${cert_num} certificate(s)"
    fi
    echo "[DEBUG] === End ${label} ==="
}

function updateCertificates {
    local CA_FILE="$1"
    if [[ -e "${CA_FILE}" && -n "${CA_FILE}" ]]; then
        debugPrintCertsFromFile "${CA_FILE}" "Certificates in source file BEFORE import (${CA_FILE})"

        local LOCAL_NAME
        LOCAL_NAME="$(basename "${CA_FILE}" | sed 's/\.[^.]*$//').crt"
        cp "${CA_FILE}" "/usr/local/share/ca-certificates/${LOCAL_NAME}"
        update-ca-certificates
        echo "certs from ${CA_FILE} added to trusted root"
        export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
        echo "export REQUESTS_CA_BUNDLE=${REQUESTS_CA_BUNDLE}" >> ~/.bashrc

        debugPrintCertsFromFile "/usr/local/share/ca-certificates/${LOCAL_NAME}" "Certificates AFTER import (installed file /usr/local/share/ca-certificates/${LOCAL_NAME})"
        [[ "${ENVGENE_LOG_LEVEL}" == "DEBUG" ]] && echo "[DEBUG] Certificate import completed successfully for ${CA_FILE}"
    else
        log "CA file ${CA_FILE} not found or empty"
        exit 1
    fi
}


function main() {
  if [ -z "${CI_PROJECT_DIR:-}" ]; then
      log "Error: CI_PROJECT_DIR is not set"
      exit 1
  fi

  # If certs_dir doesn't exist or is empty, fall back to default_cert
  if [ ! -d "$certs_dir" ] || ! find "$certs_dir" -mindepth 1 -print -quit >/dev/null 2>&1; then
      if [ -f "$default_cert" ]; then
          updateCertificates "$default_cert"
      else
          log "No certificates found and default certificate does not exist: $default_cert"
      fi
  else
      # Iterate files safely (handles spaces/newlines)
      while IFS= read -r -d '' cert; do
          updateCertificates "$cert"
      done < <(find "$certs_dir" -mindepth 1 -maxdepth 1 -type f -print0)
  fi
}

main
