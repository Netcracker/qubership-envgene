#!/bin/bash

CA_FILE="$1"
# Default log level to INFO if not set; normalize to uppercase for comparison
ENVGENE_LOG_LEVEL="${ENVGENE_LOG_LEVEL:-INFO}"
ENVGENE_LOG_LEVEL="$(printf '%s' "${ENVGENE_LOG_LEVEL}" | tr '[:lower:]' '[:upper:]')"

function getLinuxDisto {
    if [[ -f /etc/os-release ]]; then
      # freedesktop.org and systemd
      . /etc/os-release
      DIST=$NAME
    elif type lsb_release >/dev/null 2>&1; then
      # linuxbase.org
      DIST=$(lsb_release -si)
    elif [[ -f /etc/lsb-release ]]; then
      # For some versions of Debian/Ubuntu without lsb_release command
      . /etc/lsb-release
      DIST=$DISTRIB_ID
    elif [[ -f /etc/debian_version ]]; then
      # Older Debian/Ubuntu/etc.
      DIST=Debian
    else
      # Fall back to uname, e.g. "Linux <version>", also works for BSD, etc.
      DIST=$(uname -s)
    fi
    # convert to lowercase
    DIST="$(tr '[:upper:]' '[:lower:]' <<< "$DIST")"
}

function debugPrintCertsFromFile {
    local file="$1"
    local label="$2"
     # Exit early unless debug is enabled
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
          echo "[DEBUG] --- Certificate #${cert_num} in ${file} ---"
          echo "$block" | openssl x509 -noout -subject -issuer -dates 2>/dev/null || echo "[DEBUG] (openssl could not decode this block)"
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
    if [[ -e "${CA_FILE}" && ! -z "${CA_FILE}" ]]; then
      getLinuxDisto
      echo "Linux Distribution identified as: $DIST"

      # Debug: print certificates in source file BEFORE import
      debugPrintCertsFromFile "${CA_FILE}" "Certificates in source file BEFORE import (${CA_FILE})"

      # Derive destination filename from source so multiple CAs do not overwrite each other; use .crt for compatibility
      LOCAL_NAME="$(basename "${CA_FILE}" | sed 's/\.[^.]*$//').crt"
      if [[ "${DIST}" == *"debian"* || "${DIST}" == *"ubuntu"* ]]; then
        cp "${CA_FILE}" "/usr/local/share/ca-certificates/${LOCAL_NAME}"
        update-ca-certificates --fresh
        echo "certs from ${CA_FILE} added to trusted root"
        export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt #https://ubuntu.com/server/docs/install-a-root-ca-certificate-in-the-trust-store
      elif [[ "${DIST}" == *"centos"* ]]; then
        cp "${CA_FILE}" "/etc/pki/ca-trust/source/anchors/${LOCAL_NAME}"
        update-ca-trust
        echo "certs from ${CA_FILE} added to trusted root"
        export REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt #https://techjourney.net/update-add-ca-certificates-bundle-in-redhat-centos/
      elif [[ "${DIST}" == *"alpine"* ]]; then
        cp "${CA_FILE}" "/usr/local/share/ca-certificates/${LOCAL_NAME}"
        update-ca-certificates
        echo "certs from ${CA_FILE} added to trusted root"
        export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
      elif [[ "${DIST}" == *"red hat"* ]]; then
        mkdir -p /etc/pki/ca-trust/source/anchors
        cp "${CA_FILE}" "/etc/pki/ca-trust/source/anchors/${LOCAL_NAME}"
        update-ca-trust
        echo "certs from ${CA_FILE} added to trusted root"
        export REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt #https://www.redhat.com/en/blog/configure-ca-trust-list
      fi

      # Debug: print certificates AFTER import (from the installed location / bundle)
      if [[ "${DIST}" == *"debian"* || "${DIST}" == *"ubuntu"* ]]; then
        debugPrintCertsFromFile "/usr/local/share/ca-certificates/${LOCAL_NAME}" "Certificates AFTER import (installed file /usr/local/share/ca-certificates/${LOCAL_NAME})"
      elif [[ "${DIST}" == *"centos"* || "${DIST}" == *"red hat"* ]]; then
        debugPrintCertsFromFile "/etc/pki/ca-trust/source/anchors/${LOCAL_NAME}" "Certificates AFTER import (installed file /etc/pki/ca-trust/source/anchors/${LOCAL_NAME})"
      elif [[ "${DIST}" == *"alpine"* ]]; then
        debugPrintCertsFromFile "/usr/local/share/ca-certificates/${LOCAL_NAME}" "Certificates AFTER import (installed file /usr/local/share/ca-certificates/${LOCAL_NAME})"
      fi
      [[ "${ENVGENE_LOG_LEVEL}" == "DEBUG" ]] && echo "[DEBUG] Certificate import completed successfully for ${CA_FILE}"
    else
      echo "CA file ${CA_FILE} not found or empty"
      exit 1
    fi
    echo "export REQUESTS_CA_BUNDLE=${REQUESTS_CA_BUNDLE}" >> ~/.bashrc
}

updateCertificates
