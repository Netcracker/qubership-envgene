#!/usr/bin/env bash

certs_dir="${CI_PROJECT_DIR:-}/configuration/certs"
default_cert="/default_cert.pem"

if [ ! -d "$certs_dir" ] || [ -z "$(ls -A $certs_dir 2>/dev/null)" ]; then
    if [ -f "$default_cert" ]; then
        # shellcheck disable=SC1091
        . /module/scripts/update_ca_cert.sh "$default_cert"
    else
        echo "No certificates found and default certificate does not exist: $default_cert"
    fi
else
    # Iterate over files in 'certs' directory and process each
    for path in $(ls -A $certs_dir); do
        # shellcheck disable=SC1091
        . /module/scripts/update_ca_cert.sh ${certs_dir}/$path
    done
fi