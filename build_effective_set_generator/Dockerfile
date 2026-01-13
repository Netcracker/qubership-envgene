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

#STAGE 2: Minimize the CLI image
FROM registry.access.redhat.com/ubi8/ubi-minimal:8.1 AS minimized_cli

ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en'

COPY --from=cli --chown=1001:root /deployments /deployments
COPY --from=cli /etc/alternatives/jre/lib/security/java.security /etc/alternatives/jre/lib/security/java.security

RUN chmod g+rwX /deployments

USER 1001

ENTRYPOINT [ "/deployments/run-java.sh" ]

#STAGE 3: Builder
FROM python:3.12-alpine3.19 AS build

RUN apk add --update --no-cache \
    gcc \
    curl \
    musl-dev \
    libffi-dev \
    openssl-dev

# Copy configuration files
COPY build_effective_set_generator/build/pip.conf /etc/pip.conf
COPY build_effective_set_generator/build/requirements.txt /build/requirements.txt
COPY build_effective_set_generator/build/constraint.txt /build/constraint.txt

# Create virtual environment and install Python packages
RUN python -m venv /module/venv
RUN /module/venv/bin/pip install --upgrade pip setuptools wheel
RUN /module/venv/bin/pip install --no-cache-dir --retries 10 --timeout 60 -r /build/requirements.txt
