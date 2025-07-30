#######################################
# Stage 1 
FROM ghcr.io/netcracker/qubership-base-module-dockerimage:v2.0.0 AS build

USER root

COPY python/integration /python/integration
COPY schemas /module/schemas
COPY python /python
COPY build_gcip/build/pip.conf /etc/pip.conf
COPY build_gcip/build/requirements.txt /build/requirements.txt
COPY build_gcip/scripts /module/scripts
COPY build_gcip/pipegene_plugins /module/scripts/pipegene_plugins

RUN apk update \
    && apk add --no-cache \
        git \
        gcc \
        musl-dev \
        libffi-dev \
        curl \
        bash \
    && test -d /module/venv || python3 -m venv /module/venv \
    && source /module/venv/bin/activate \
    && python3 -m pip install --upgrade pip setuptools wheel \
    && pip install --no-deps --no-cache-dir -r /build/requirements.txt \
    && python3 -m pip install /python/integration \
    && python3 -m pip install /python/jschon-sort \
    && python3 -m pip install /python/envgene \
    && python3 -m pip install PyYAML

#######################################
# Stage 2
FROM ghcr.io/netcracker/qubership-base-module-dockerimage:v2.0.0

COPY --from=build /module /module

ENV PATH=/module/venv/bin:/usr/bin:/usr/local/bin:$PATH

USER ci:ci
