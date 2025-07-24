#######################################
# Stage 1 
FROM ghcr.io/netcracker/qubership-base-module-dockerimage:v2.0.0

USER root

COPY build_effective_set_generator/build/pip.conf /etc/pip.conf
COPY build_effective_set_generator/build/requirements.txt /build/requirements.txt
COPY build_effective_set_generator/build/requirements.yml /build/requirements.yml
COPY build_effective_set_generator/scripts /module/scripts
COPY build_effective_set_generator/ansible /module/ansible
COPY python /python
COPY schemas /module/schemas
COPY python/integration /python/integration
ENV ANSIBLE_LIBRARY /module/ansible/library:$ANSIBLE_LIBRARY

RUN apk update \
    && apk add --update --no-cache \
        git \
        gcc \
        musl-dev \
        libffi-dev \
        sudo \
        curl \
    && curl --retry 3 --retry-connrefused --retry-delay 5 -LO https://github.com/mozilla/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 \
    && chmod +x sops-v3.9.0.linux.amd64 \
    && mv sops-v3.9.0.linux.amd64 /usr/local/bin/sops \
    && test -d /module/venv || python3 -m venv /module/venv \
    && source /module/venv/bin/activate \
    && . /module/venv/bin/activate \
    && pip install --no-deps --no-cache-dir -r /build/requirements.txt \
    && pip install ansible --upgrade \
    && ansible-galaxy collection install -r /build/requirements.yml -p /module/ansible/collections \
    && python3 -m pip install /python/integration \
    && python3 -m pip install /python/jschon-sort \
    && python3 -m pip install /python/envgene \
    && chmod 744 /module/scripts/*
