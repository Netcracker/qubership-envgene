#########################################
## Stage 1: Builder
FROM ghcr.io/netcracker/base-images-module-base:main as builder

USER root

# Copy only files needed for installation first to leverage Docker cache
COPY build_envgene/build/pip.conf /etc/pip.conf
COPY build_envgene/build/requirements.txt /build/requirements.txt
COPY build_envgene/build/requirements.yml /build/requirements.yml

# Install build dependencies and runtime packages in a single layer
RUN apk update && \
    apk add --no-cache \
        git \
        python3 \
        py3-pip \
        py3-cryptography \
        py3-openssl \
        openssh-client \
        ca-certificates \
        coreutils \
        curl \
        sudo \
        zip \
        unzip \
        jq \
        # Build dependencies
        build-base \
        libxml2-dev \
        libxslt-dev \
        zlib-dev && \
    # Install sops
    curl --retry 3 --retry-connrefused --retry-delay 5 -LO https://github.com/mozilla/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 && \
    chmod +x sops-v3.9.0.linux.amd64 && \
    mv sops-v3.9.0.linux.amd64 /usr/local/bin/sops && \
    # Install Python packages
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /build/requirements.txt && \
    pip install --no-cache-dir ansible --upgrade && \
    rm -rf /usr/lib/python3.10/site-packages/ansible_collections/* && \
    ansible-galaxy collection install -r /build/requirements.yml -p /module/ansible/collections && \
    pip install --no-cache-dir PyYAML && \
    # Cleanup
    apk del build-base libxml2-dev libxslt-dev zlib-dev && \
    rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache

# Copy remaining application files
COPY build_envgene/ansible /module/ansible
COPY build_envgene/scripts /module/scripts
COPY build_envgene/workflows /workflows
COPY python /python

COPY build_* create_* produce_* sort* /build_env/
COPY scripts /build_env/scripts
COPY env-builder /build_env/env-builder
COPY schemas /build_env/schemas

# Install local Python packages
RUN pip install --no-cache-dir \
    /python/jschon-sort \
    /python/envgene \
    /python/integration && \
    chmod 754 /module/scripts/* && \
    # Cleanup pip cache
    rm -rf /root/.cache

ENV ANSIBLE_LIBRARY=/module/ansible/library:$ANSIBLE_LIBRARY

WORKDIR /module/ansible
