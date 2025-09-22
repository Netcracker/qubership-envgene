#!/bin/bash

CA_FILE="$1"

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

function updateCertificates {
    if [[ -e "${CA_FILE}" && ! -z "${CA_FILE}" ]]; then
      getLinuxDisto
      echo "Linux Distribution identified as: $DIST"
      if [[ "${DIST}" == *"debian"* || "${DIST}" == *"ubuntu"* ]]; then
        cp "${CA_FILE}" /usr/local/share/ca-certificates/
        update-ca-certificates --fresh
        echo "certs from ${CA_FILE} added to trusted root"
        export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt #https://ubuntu.com/server/docs/install-a-root-ca-certificate-in-the-trust-store
      elif [[ "${DIST}" == *"centos"* ]]; then
        cp "${CA_FILE}" /etc/pki/ca-trust/source/anchors/ca.crt
        update-ca-trust
        echo "certs from ${CA_FILE} added to trusted root"
        export REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt #https://techjourney.net/update-add-ca-certificates-bundle-in-redhat-centos/
      elif [[ "${DIST}" == *"alpine"* ]]; then
        cat "${CA_FILE}" >> /etc/ssl/certs/ca-certificates.crt
        echo "certs from ${CA_FILE} added to trusted root"
        export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt #we copy the certs to this file in line 43
      elif [[ "${DIST}" == *"red hat"* ]]; then
        mkdir -p /etc/pki/ca-trust/source/anchors
        cp "${CA_FILE}" /etc/pki/ca-trust/source/anchors/
        update-ca-trust
        echo "certs from ${CA_FILE} added to trusted root"
        export REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt #https://www.redhat.com/en/blog/configure-ca-trust-list
      fi
    else
      echo "CA file ${CA_FILE} not found or empty"
      exit 1
    fi
    echo "export REQUESTS_CA_BUNDLE=${REQUESTS_CA_BUNDLE}" >> ~/.bashrc
}

updateCertificates
