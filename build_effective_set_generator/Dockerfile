#STAGE 1: CLI
# checkov:skip=CKV2_DOCKER_1:sudo is required for certain operations in scripts
# hadolint ignore=DL3018

FROM registry.access.redhat.com/ubi8/ubi-minimal:8.1 AS cli

ARG JAVA_PACKAGE=java-17-openjdk-headless
ARG RUN_JAVA_VERSION=1.3.8

# hadolint ignore=DL3041
RUN microdnf install -y curl ca-certificates ${JAVA_PACKAGE} && \
    microdnf clean all && \
    mkdir -p /deployments && \
    curl -s https://repo1.maven.org/maven2/io/fabric8/run-java-sh/${RUN_JAVA_VERSION}/run-java-sh-${RUN_JAVA_VERSION}-sh.sh -o /deployments/run-java.sh && \
    chmod 540 /deployments/run-java.sh && \
    echo "securerandom.source=file:/dev/urandom" >> /etc/alternatives/jre/lib/security/java.security

COPY build_effective_set_generator/effective-set-generator/target/*.jar /deployments/app.jar

#STAGE 2: Builder
FROM python:3.12-alpine3.19 AS build

# hadolint ignore=DL3018
RUN apk add --update --no-cache \
    gcc \
    curl \
    musl-dev \
    libffi-dev \
    openssl-dev

# Copy configuration files
COPY build_effective_set_generator/build/configuration/pip.conf /etc/pip.conf
COPY build_effective_set_generator/build/configuration/requirements.txt /build/requirements.txt
COPY build_effective_set_generator/build/configuration/constraint.txt /build/constraint.txt

# Create virtual environment and install Python packages
RUN python -m venv /module/venv && \
    /module/venv/bin/pip install --upgrade pip setuptools wheel && \
    /module/venv/bin/pip install --no-cache-dir --retries 10 --timeout 60 -r /build/requirements.txt

# Download and install SOPS for secrets management
RUN wget --quiet --tries=3 \
    https://github.com/mozilla/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 \
    -O /usr/local/bin/sops && \
    chmod +x /usr/local/bin/sops


# Aggressive cleanup to reduce image size
RUN apk del gcc musl-dev libffi-dev openssl-dev && \
    rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache
# Remove unnecessary files from Python packages
RUN find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyo' -delete && \
    find /module/venv/lib/python3.12/site-packages -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true


#STAGE 3: Runtime
FROM python:3.12-alpine3.19 AS runtime

ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en'

COPY --from=cli --chown=1001:root /deployments /deployments
COPY --from=cli /etc/alternatives/jre/lib/security/java.security /etc/alternatives/jre/lib/security/java.security

RUN chmod g+rwX /deployments

COPY build_effective_set_generator/build/configuration/pip.conf /etc/pip.conf
COPY build_effective_set_generator/build/configuration/constraint.txt /build/constraint.txt
COPY build_effective_set_generator/build/configuration/sources.list /etc/apk/repositories

# hadolint ignore=DL3018
RUN apk add --no-cache \
    bash \
    ca-certificates \
    tar \
    curl \
    jq \
    yq \
    gettext \
    sed \
    age

COPY --from=build /usr/local/bin/sops /usr/local/bin/sops
COPY build_effective_set_generator/build/scripts /module/scripts

RUN addgroup ci && adduser -D -h /module/ -s /bin/bash -G ci ci && \
    chown ci:ci -R /module && \
    chmod +x /module/scripts/*.sh && \
    chmod 644 /module/scripts/*.py 2>/dev/null || true && \
    chmod +x /usr/local/bin/sops

ENV PATH=/module/venv/bin:$PATH

USER ci:ci

ENTRYPOINT [""]
