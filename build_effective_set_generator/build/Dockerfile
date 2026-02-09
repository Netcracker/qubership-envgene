FROM python:3.12-alpine3.19 AS build

ARG RUN_JAVA_VERSION=1.3.8
ARG SOPS_VERSION=3.9.0

# hadolint ignore=DL3018
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

COPY build_effective_set_generator/build/sources.list /etc/apk/repositories
COPY build_effective_set_generator/build/pip.conf /etc/pip.conf
COPY build_effective_set_generator/build/requirements.txt /build/requirements.txt
COPY build_effective_set_generator/build/requirements.yml /build/requirements.yml
COPY python /python

RUN python3 -m venv /module/venv && \
    /module/venv/bin/pip install --upgrade pip "setuptools<82" wheel

RUN /module/venv/bin/pip install --no-cache-dir \
    --no-binary cffi \
    --no-binary cryptography \
    -r /build/requirements.txt

RUN /module/venv/bin/pip install --no-cache-dir \
    /python/integration \
    /python/jschon-sort \
    /python/envgene \
    /python/artifact-searcher

RUN curl -fsSL \
    https://github.com/mozilla/sops/releases/download/v${SOPS_VERSION}/sops-v${SOPS_VERSION}.linux.amd64 \
    -o /usr/local/bin/sops && \
    chmod +x /usr/local/bin/sops

RUN mkdir -p /deployments && \
    curl -sSL https://repo1.maven.org/maven2/io/fabric8/run-java-sh/${RUN_JAVA_VERSION}/run-java-sh-${RUN_JAVA_VERSION}-sh.sh \
    -o /deployments/run-java.sh

COPY build_effective_set_generator/effective-set-generator/target/*.jar /deployments/app.jar


FROM python:3.12-alpine3.19 AS runtime

ARG JAVA_PACKAGE=openjdk17-jre-headless

ENV LANG='en_US.UTF-8' \
    LANGUAGE='en_US:en' \
    PATH=/module/venv/bin:$PATH

COPY build_effective_set_generator/build/pip.conf /etc/pip.conf
COPY build_effective_set_generator/build/sources.list /etc/apk/repositories

# Install ONLY runtime dependencies (NO dev packages)
# hadolint ignore=DL3018
RUN apk add --no-cache \
    libffi \
    libgcc \
    openssl \
    bash \
    ca-certificates \
    tar \
    curl \
    jq \
    yq \
    gettext \
    sed \
    age \
    ${JAVA_PACKAGE}

COPY --from=build /python /python
COPY --from=build /module/venv /module/venv
COPY --from=build /usr/local/bin/sops /usr/local/bin/sops
COPY --from=build /deployments /deployments

COPY scripts/build_env/ /build_env/scripts/build_env/
COPY scripts/build_env/process_sd.py /module/scripts/
COPY build_effective_set_generator/scripts/ /module/scripts/
COPY scripts/utils/ /module/scripts/utils/

# cert script should be moved to scripts/utils/
COPY build_envgene/scripts/handle_certs.sh /module/scripts/

# User creation + permissions
RUN addgroup ci && \
    adduser -D -h /module/ -s /bin/bash -G ci ci && \
    chown ci:ci -R /module /deployments && \
    chmod +x /module/scripts/*.sh && \
    chmod 644 /module/scripts/*.py 2>/dev/null || true && \
    chmod +x /usr/local/bin/sops && \
    chmod 540 /deployments/run-java.sh && \
    chmod g+rwX /deployments

USER ci:ci
    
WORKDIR /module
