# ═══════════════════════════════════════════════════════════════════════════════════
# Stage 1: Build
# ═══════════════════════════════════════════════════════════════════════════════════
FROM ghcr.io/netcracker/qubership-envgene-base-modules:1.0.0 AS build

ARG RUN_JAVA_VERSION=1.3.8

# hadolint ignore=DL3018
RUN apk add --no-cache \
    libffi-dev \
    openssl-dev \
    python3-dev \
    cargo \
    rust \
    build-base

COPY build_effective_set_generator/build/pip.conf /etc/pip.conf
COPY build_effective_set_generator/build/requirements.txt /build/requirements.txt
COPY python /python

RUN pip install --no-cache-dir \
    --no-binary cffi \
    --no-binary cryptography \
    -r /build/requirements.txt
    
RUN pip install --no-cache-dir \
    /python/integration \
    /python/jschon-sort \
    /python/envgene \
    /python/artifact-searcher

RUN mkdir -p /deployments && \
    curl -sSL https://repo1.maven.org/maven2/io/fabric8/run-java-sh/${RUN_JAVA_VERSION}/run-java-sh-${RUN_JAVA_VERSION}-sh.sh \
    -o /deployments/run-java.sh

COPY build_effective_set_generator/effective-set-generator/target/*.jar /deployments/app.jar


# ═══════════════════════════════════════════════════════════════════════════════════
# Stage 2: Runtime
# ═══════════════════════════════════════════════════════════════════════════════════
FROM ghcr.io/netcracker/qubership-envgene-base-modules:1.0.0 AS runtime

ARG JAVA_PACKAGE=openjdk17-jre-headless

ENV LANG='en_US.UTF-8' \
    LANGUAGE='en_US:en'

# Install ONLY runtime dependencies (NO dev packages)
# hadolint ignore=DL3018
RUN apk add --no-cache \
    libgcc \
    ${JAVA_PACKAGE}

COPY --from=build /python /python
COPY --from=build /module/venv /module/venv
COPY --from=build /deployments /deployments

COPY scripts/build_env/ /build_env/scripts/build_env/
COPY build_effective_set_generator/scripts/ /module/scripts/
COPY scripts/utils/ /module/scripts/utils/

# Permissions
RUN chown -R ci:ci /module /deployments && \
    chmod +x /module/scripts/*.sh && \
    chmod 644 /module/scripts/*.py 2>/dev/null || true && \
    chmod 540 /deployments/run-java.sh && \
    chmod g+rwX /deployments

USER ci:ci
WORKDIR /module
