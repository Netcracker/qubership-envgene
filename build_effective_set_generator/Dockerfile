#############################################
# STAGE 1: CLI (UBI minimal runtime with Java)
#############################################
FROM registry.access.redhat.com/ubi8/ubi-minimal:8.1 AS cli

ARG JAVA_PACKAGE=java-17-openjdk-headless
ARG RUN_JAVA_VERSION=1.3.8

RUN microdnf install -y curl ca-certificates ${JAVA_PACKAGE} && \
    microdnf clean all && \
    mkdir -p /deployments && \
    curl -sSf https://repo1.maven.org/maven2/io/fabric8/run-java-sh/${RUN_JAVA_VERSION}/run-java-sh-${RUN_JAVA_VERSION}-sh.sh \
        -o /deployments/run-java.sh && \
    chmod 540 /deployments/run-java.sh && \
    echo "securerandom.source=file:/dev/urandom" >> /etc/alternatives/jre/lib/security/java.security

COPY build_effective_set_generator/effective-set-generator/target/*.jar /deployments/app.jar



#############################################
# STAGE 2: Build Python Environment (Alpine)
#############################################
FROM python:3.12-alpine3.19 AS build

# Install ALL system-level *build dependencies*
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    python3-dev \
    cargo \
    rust \
    build-base \
    curl \
    wget

COPY build_effective_set_generator/build/configuration/pip.conf /etc/pip.conf
COPY build_effective_set_generator/build/configuration/requirements.txt /build/requirements.txt
COPY build_effective_set_generator/build/configuration/constraint.txt /build/constraint.txt

# Build Python virtual environment
RUN python3 -m venv /module/venv && \
    /module/venv/bin/pip install --upgrade pip setuptools wheel && \
    /module/venv/bin/pip install --no-cache-dir --no-binary cffi --no-binary cryptography \
        -r /build/requirements.txt

# Install SOPS
RUN wget --quiet --tries=3 \
    https://github.com/mozilla/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 \
    -O /usr/local/bin/sops && \
    chmod +x /usr/local/bin/sops

# DO NOT delete build dependencies here — runtime needs them indirectly




#############################################
# STAGE 3: Final Runtime (Alpine)
#############################################
FROM python:3.12-alpine3.19 AS runtime

ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en'

COPY --from=cli --chown=1001:root /deployments /deployments
COPY --from=cli /etc/alternatives/jre/lib/security/java.security \
     /etc/alternatives/jre/lib/security/java.security

RUN chmod g+rwX /deployments

COPY build_effective_set_generator/build/configuration/pip.conf /etc/pip.conf
COPY build_effective_set_generator/build/configuration/constraint.txt /build/constraint.txt
COPY build_effective_set_generator/build/configuration/sources.list /etc/apk/repositories

# Install ONLY runtime dependencies (NO dev packages)
RUN apk add --no-cache \
    libffi \
    openssl \
    bash \
    ca-certificates \
    tar \
    curl \
    jq \
    yq \
    gettext \
    sed \
    age

# Bring the virtual environment compiled in build stage
COPY --from=build /module/venv /module/venv

COPY build_effective_set_generator/build/scripts /module/scripts
COPY scripts/utils /module/scripts/utils

# User creation + permissions
RUN addgroup ci && adduser -D -h /module/ -s /bin/bash -G ci ci && \
    chown ci:ci -R /module && \
    chmod +x /module/scripts/*.sh && \
    chmod 644 /module/scripts/*.py 2>/dev/null || true && \
    chmod +x /usr/local/bin/sops

ENV PATH=/module/venv/bin:$PATH

USER ci:ci

ENTRYPOINT [""]
