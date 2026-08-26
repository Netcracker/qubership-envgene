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
    if [[ "${ENVGENE_LOG_LEVEL}" != "DEBUG" ]]; then
        return 0
    fi
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

validate_bundle() {
    local file="$1"
    local count=0
    local failed=0
    local tmpdir
    tmpdir=$(mktemp -d)

    awk -v dir="$tmpdir" '
        /-----BEGIN CERTIFICATE-----/ { n++; out = dir "/cert-" n ".pem" }
        out { print > out }
        /-----END CERTIFICATE-----/ { close(out); out="" }
    ' "$file"

    for part in "$tmpdir"/cert-*.pem; do
        [[ -s "$part" ]] || continue
        count=$((count + 1))
        if ! openssl x509 -in "$part" -noout -checkend 0 2>/dev/null; then
            log "[WARNING]: Certificate #$count in ${file} is expired or invalid"
            failed=1
        fi
    done

    rm -rf "$tmpdir"

    if [[ $count -eq 0 ]]; then
        log "[WARNING]: No valid PEM certificate blocks found in ${file}"
        failed=1
    fi

    return $failed
}

function updateCertificates {
    local CA_FILE="$1"
    if [[ -e "${CA_FILE}" && -n "${CA_FILE}" ]]; then
        debugPrintCertsFromFile "${CA_FILE}" "Certificates in source file BEFORE import (${CA_FILE})"

        if ! validate_bundle "${CA_FILE}"; then
            log "[ERROR]: Certificate validation failed for ${CA_FILE}"
            exit 1
        fi

        local LOCAL_NAME
        LOCAL_NAME="$(basename "${CA_FILE}" | sed 's/\.[^.]*$//').crt"
        cp "${CA_FILE}" "/usr/local/share/ca-certificates/${LOCAL_NAME}"
        update-ca-certificates
        echo "certs from ${CA_FILE} added to trusted root"
        export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
        echo "export REQUESTS_CA_BUNDLE=${REQUESTS_CA_BUNDLE}" >> ~/.bashrc

        debugPrintCertsFromFile "/usr/local/share/ca-certificates/${LOCAL_NAME}" "Certificates AFTER import (installed file /usr/local/share/ca-certificates/${LOCAL_NAME})"
        log "[INFO] Certificate import completed successfully for ${CA_FILE}"
    else
        log "[WARNING]: CA file ${CA_FILE} not found or empty, skipping"
        return 0
    fi
}


function main() {
  if [ -z "${CI_PROJECT_DIR:-}" ]; then
      log "[Error]: CI_PROJECT_DIR is not set"
      exit 1
  fi

  local certs_applied=0

  # Install SSL_CERTIFICATES_BUNDLE if provided
  if [ -n "${SSL_CERTIFICATES_BUNDLE:-}" ]; then
      log "[INFO]: SSL_CERTIFICATES_BUNDLE is set, installing..."
      local BUNDLE_FILE
      BUNDLE_FILE=$(mktemp /tmp/ssl_bundle_XXXXXX)
      if ! echo "${SSL_CERTIFICATES_BUNDLE}" | base64 -d > "${BUNDLE_FILE}" 2>/dev/null; then
          rm -f "${BUNDLE_FILE}"
          log "[ERROR]: SSL_CERTIFICATES_BUNDLE is not valid base64"
          exit 1
      fi
      updateCertificates "${BUNDLE_FILE}"
      rm -f "${BUNDLE_FILE}"
      certs_applied=1
  else
      log "[INFO]: SSL_CERTIFICATES_BUNDLE is not set, skipping"
  fi

  # Install certs from certs_dir if it exists and has files
  if [ -d "$certs_dir" ] && find "$certs_dir" -mindepth 1 -print -quit >/dev/null 2>&1; then
      log "[INFO]: Found certificates in $certs_dir, installing..."
      while IFS= read -r -d '' cert; do
          log "[INFO]: Installing certificate: $cert"
          updateCertificates "$cert"
      done < <(find "$certs_dir" -mindepth 1 -maxdepth 1 -type f -print0)
      certs_applied=1
  else
      log "[INFO]: No certificates found in $certs_dir, skipping"
  fi

  # If neither SSL_CERTIFICATES_BUNDLE nor certs_dir provided anything, fall back to default_cert
  if [ "$certs_applied" -eq 0 ]; then
      if [ -f "$default_cert" ]; then
          log "[INFO]: Falling back to default certificate: $default_cert"
          updateCertificates "$default_cert"
      else
          log "[INFO]: No certificates found and default certificate does not exist: $default_cert"
      fi
  fi
}

main
