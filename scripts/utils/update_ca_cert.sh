#!/bin/bash

CA_FILE="$1"

# Default log level to INFO if not set; normalize to uppercase
ENVGENE_LOG_LEVEL="${ENVGENE_LOG_LEVEL:-INFO}"
ENVGENE_LOG_LEVEL="$(printf '%s' "${ENVGENE_LOG_LEVEL}" | tr '[:lower:]' '[:upper:]')"

function getLinuxDisto {
    if [[ -f /etc/os-release ]]; then
      . /etc/os-release
      DIST=$NAME
    elif type lsb_release >/dev/null 2>&1; then
      DIST=$(lsb_release -si)
    elif [[ -f /etc/lsb-release ]]; then
      . /etc/lsb-release
      DIST=$DISTRIB_ID
    elif [[ -f /etc/debian_version ]]; then
      DIST=Debian
    else
      DIST=$(uname -s)
    fi
    DIST="$(tr '[:upper:]' '[:lower:]' <<< "$DIST")"
}

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

    while IFS= read -r line; do
      if [[ "$line" == "-----BEGIN CERTIFICATE-----" ]]; then
        block="$line"
        continue
      fi

      if [[ -n "$block" ]]; then
        block+=$'\n'"$line"
        if [[ "$line" == "-----END CERTIFICATE-----" ]]; then
          cert_num=$((cert_num + 1))
          echo "[DEBUG] --- Certificate #${cert_num} ---"
          echo "$block" | openssl x509 -noout -subject -issuer -dates 2>/dev/null \
            || echo "[DEBUG] Could not decode certificate"
          block=""
        fi
      fi
    done < "$file"

    [[ $cert_num -eq 0 ]] && echo "[DEBUG] No certificates found"
    echo "[DEBUG] Total: ${cert_num}"
    echo "[DEBUG] === End ${label} ==="
}

function persistEnvVar {
    local var_name="$1"
    local var_value="$2"

    # Remove existing entry to avoid duplicates
    sed -i "/export ${var_name}=/d" ~/.bashrc

    # Add updated value
    echo "export ${var_name}=${var_value}" >> ~/.bashrc
}

function updateCertificates {
    if [[ -z "${CA_FILE}" || ! -e "${CA_FILE}" ]]; then
      echo "CA file ${CA_FILE} not found or empty"
      exit 1
    fi

    getLinuxDisto
    echo "Linux Distribution identified as: $DIST"

    debugPrintCertsFromFile "${CA_FILE}" "Certificates BEFORE import"

    LOCAL_NAME="$(basename "${CA_FILE}" | sed 's/\.[^.]*$//').crt"

    if [[ "${DIST}" == *"debian"* || "${DIST}" == *"ubuntu"* || "${DIST}" == *"alpine"* ]]; then
        DEST_PATH="/usr/local/share/ca-certificates/${LOCAL_NAME}"
        cp "${CA_FILE}" "${DEST_PATH}"
        update-ca-certificates --fresh 2>/dev/null || update-ca-certificates
        BUNDLE_PATH="/etc/ssl/certs/ca-certificates.crt"

    elif [[ "${DIST}" == *"centos"* || "${DIST}" == *"red hat"* ]]; then
        DEST_DIR="/etc/pki/ca-trust/source/anchors"
        mkdir -p "${DEST_DIR}"
        DEST_PATH="${DEST_DIR}/${LOCAL_NAME}"
        cp "${CA_FILE}" "${DEST_PATH}"
        update-ca-trust
        BUNDLE_PATH="/etc/pki/tls/certs/ca-bundle.crt"
    else
        echo "Unsupported distribution: $DIST"
        exit 1
    fi

    echo "Certificates from ${CA_FILE} added to trusted root"

    # ✅ Set ALL relevant environment variables
    export REQUESTS_CA_BUNDLE="${BUNDLE_PATH}"
    export CURL_CA_BUNDLE="${BUNDLE_PATH}"
    export SSL_CERT_FILE="${BUNDLE_PATH}"

    echo "Environment variables set:"
    echo "  REQUESTS_CA_BUNDLE=${REQUESTS_CA_BUNDLE}"
    echo "  CURL_CA_BUNDLE=${CURL_CA_BUNDLE}"
    echo "  SSL_CERT_FILE=${SSL_CERT_FILE}"

    # ✅ Persist them
    persistEnvVar "REQUESTS_CA_BUNDLE" "${REQUESTS_CA_BUNDLE}"
    persistEnvVar "CURL_CA_BUNDLE" "${CURL_CA_BUNDLE}"
    persistEnvVar "SSL_CERT_FILE" "${SSL_CERT_FILE}"

    debugPrintCertsFromFile "${DEST_PATH}" "Certificates AFTER import"

    [[ "${ENVGENE_LOG_LEVEL}" == "DEBUG" ]] && \
      echo "[DEBUG] Certificate import completed successfully"
}

updateCertificates
