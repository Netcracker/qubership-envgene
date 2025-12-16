#######################################
# Stage 1
FROM ghcr.io/netcracker/qubership-base-module-dockerimage:v2.0.0
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]

USER root

COPY build_effective_set_generator/build/pip.conf /etc/pip.conf
COPY build_effective_set_generator/build/requirements.txt /build/requirements.txt
COPY build_effective_set_generator/build/requirements.yml /build/requirements.yml
COPY build_effective_set_generator/scripts /module/scripts
COPY build_effective_set_generator/ansible /module/ansible
COPY python /python
COPY schemas /module/schemas
COPY python/integration /python/integration
COPY scripts /scripts
ENV ANSIBLE_LIBRARY=/module/ansible/library:$ANSIBLE_LIBRARY

RUN set -eux; \
    apk update; \
    ver() { apk list --verbose --available "$1" | head -n1 | sed -E "s/^$1-//; s/ .*//"; }; \
    apk add --no-cache \
        git="$(ver git)" \
        gcc="$(ver gcc)" \
        musl-dev="$(ver musl-dev)" \
        libffi-dev="$(ver libffi-dev)" \
        curl="$(ver curl)"; \
    curl --fail --show-error --location --retry 3 \
        -o /usr/local/bin/sops \
        https://github.com/mozilla/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 \
    && chmod +x /usr/local/bin/sops \
    && python3 -m venv /module/venv \
    && /module/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
    && /module/venv/bin/pip install --no-deps --no-cache-dir -r /build/requirements.txt \
    && /module/venv/bin/pip install --no-cache-dir --upgrade ansible \
    && /module/venv/bin/ansible-galaxy collection install -r /build/requirements.yml -p /module/ansible/collections \
    && /module/venv/bin/pip install /python/integration /python/jschon-sort /python/envgene \
    && find /module -type d -exec chmod 755 {} + \
    && find /module -type f -exec chmod 644 {} + \
    && chmod -R 755 /module/scripts

# Run container as non-root user to satisfy security best practices
# The base image already contains user and group `ci`
USER ci:ci
