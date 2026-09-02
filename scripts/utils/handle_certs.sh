#!/bin/bash
set -euo pipefail

default_cert="/default_cert.pem"
ca_bundle_dir="${CI_PROJECT_DIR}/ca_bundle"
certs_dir="${CI_PROJECT_DIR:-}/configuration/certs"

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
    local label="$2"
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
            log "[WARNING]: Certificate #$count in ${label} is expired or invalid"
            failed=1
        fi
    done

    rm -rf "$tmpdir"

    if [[ $count -eq 0 ]]; then
        log "[WARNING]: No valid PEM certificate blocks found in ${label}"
        failed=1
    fi

    return $failed
}

function updateCertificates {
    local CA_FILE="$1"
    local LABEL="${2:-$CA_FILE}"
    if [[ -e "${CA_FILE}" && -n "${CA_FILE}" ]]; then
        debugPrintCertsFromFile "${CA_FILE}" "Certificates in source file BEFORE import (${CA_FILE})"

        if ! validate_bundle "${CA_FILE}" "${LABEL}"; then
            log "[ERROR]: Certificate validation failed for '${LABEL}'"
            exit 1
        fi

        local LOCAL_NAME
        LOCAL_NAME="$(basename "${CA_FILE}" | sed 's/\.[^.]*$//').crt"
        cp "${CA_FILE}" "/usr/local/share/ca-certificates/${LOCAL_NAME}"
        update-ca-certificates
        echo "certs from '${LABEL}' added to trusted root"
        export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
        echo "export REQUESTS_CA_BUNDLE=${REQUESTS_CA_BUNDLE}" >> ~/.bashrc

        debugPrintCertsFromFile "/usr/local/share/ca-certificates/${LOCAL_NAME}" "Certificates AFTER import (installed file /usr/local/share/ca-certificates/${LOCAL_NAME})"
        log "[INFO] Certificate import completed successfully for '${LABEL}'"
    else
        log "[WARNING]: CA file '${LABEL}' not found or empty, skipping"
        return 0
    fi
}

function installCertsFromDir {
    local dir="$1"
    while IFS= read -r -d '' cert; do
        log "[INFO]: Installing certificate: $cert"
        updateCertificates "$cert" "$(basename "$cert") (from ${dir})"
    done < <(find "$dir" -mindepth 1 -maxdepth 1 -type f -print0)
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

        if printf '%s' "${SSL_CERTIFICATES_BUNDLE}" | grep -q "BEGIN CERTIFICATE"; then
            log "[ERROR]: SSL_CERTIFICATES_BUNDLE appears to contain raw PEM content, not base64. Please base64-encode your certificate bundle before setting this variable."
            exit 1
        fi

        local BUNDLE_FILE
        BUNDLE_FILE=$(mktemp /tmp/ssl_bundle_XXXXXX)
        if ! echo "${SSL_CERTIFICATES_BUNDLE}" | base64 -d > "${BUNDLE_FILE}" 2>/dev/null; then
            rm -f "${BUNDLE_FILE}"
            log "[ERROR]: SSL_CERTIFICATES_BUNDLE is not valid base64"
            exit 1
        fi
        updateCertificates "${BUNDLE_FILE}" "SSL_CERTIFICATES_BUNDLE"
        rm -f "${BUNDLE_FILE}"
        certs_applied=1
    else
        log "[INFO]: SSL_CERTIFICATES_BUNDLE is not set, skipping"
    fi

    # Install certs from ca_bundle_dir if it exists and has files
    if [ -d "$ca_bundle_dir" ] && find "$ca_bundle_dir" -mindepth 1 -print -quit >/dev/null 2>&1; then
        log "[INFO]: Found certificates in $ca_bundle_dir, installing..."
        installCertsFromDir "$ca_bundle_dir"
        certs_applied=1
    else
        log "[INFO]: No certificates found in $ca_bundle_dir, skipping"
    fi

    # Install certs from certs_dir if it exists and has files
    if [ -d "$certs_dir" ] && find "$certs_dir" -mindepth 1 -print -quit >/dev/null 2>&1; then
        log "[INFO]: Found certificates in $certs_dir, installing..."
        installCertsFromDir "$certs_dir"
        certs_applied=1
    else
        log "[INFO]: No certificates found in $certs_dir, skipping"
    fi

    # Fall back to default_cert if no certificate provided
    if [ "$certs_applied" -eq 0 ]; then
        if [ -f "$default_cert" ]; then
            log "[INFO]: Falling back to default certificate: $default_cert"
            updateCertificates "$default_cert" "default certificate (${default_cert})"
        else
            log "[INFO]: No certificates found and default certificate does not exist: $default_cert"
        fi
    fi
}

main