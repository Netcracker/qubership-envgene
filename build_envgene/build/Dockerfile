#########################################
## Stage 1
FROM ghcr.io/netcracker/qubership-base-module-dockerimage:v2.0.0 as base-image

USER root

COPY build_envgene/build/pip.conf /etc/pip.conf
COPY build_envgene/build/requirements.txt /build/requirements.txt
COPY build_envgene/build/requirements.yml /build/requirements.yml
COPY build_envgene/ansible /module/ansible
COPY build_envgene/scripts /module/scripts
COPY build_envgene/workflows /workflows
COPY python /python

COPY build_* create_* produce_* sort* /build_env/
COPY scripts /build_env/scripts
COPY env-builder /build_env/env-builder
COPY schemas /build_env/schemas


ENV ANSIBLE_LIBRARY /module/ansible/library:$ANSIBLE_LIBRARY


RUN apk update \
    && apk add --no-cache \
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
        build-base \
        libxml2-dev \
        libxslt-dev \
        zlib-dev \
        jq \
    && curl --retry 3 --retry-connrefused --retry-delay 5 -LO https://github.com/mozilla/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 \
    && chmod +x sops-v3.9.0.linux.amd64 \
    && mv sops-v3.9.0.linux.amd64 /usr/local/bin/sops \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r /build/requirements.txt \
    && pip install ansible --upgrade \
    && rm -rf /usr/lib/python3.10/site-packages/ansible_collections/* \
    && ansible-galaxy collection install -r /build/requirements.yml -p /module/ansible/collections \
    && pip install /python/jschon-sort \
    && pip install /python/envgene \
    && pip install /python/integration \
    && pip install /python/artifact-searcher \
    && chmod 754 /module/scripts/* \
    && apk del build-base libxml2-dev libxslt-dev zlib-dev \
    && rm -rf /var/cache/apk/* /tmp/* /var/tmp/* \
    && pip install PyYAML

WORKDIR /module/ansible
