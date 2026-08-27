# ═══════════════════════════════════════════════════════════════════════════════════
# Stage 1: Build
# ═══════════════════════════════════════════════════════════════════════════════════
FROM ghcr.io/netcracker/qubership-envgene-base-modules:fix_vulnerabilities AS build

ARG RUN_JAVA_VERSION=1.3.8

# hadolint ignore=DL3018
RUN apk add --no-cache \
    libffi-dev=3.4.6-r0 \
    openssl-dev=3.3.7-r0 \
    python3-dev=3.12.13-r0 \
    cargo=1.78.0-r1 \
    rust=1.78.0-r1 \
    build-base=0.5-r3

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
FROM ghcr.io/netcracker/qubership-envgene-base-modules:fix_vulnerabilities AS runtime

ARG JAVA_PACKAGE=openjdk17-jre-headless=17.0.16_p8-r0

ENV LANG='en_US.UTF-8' \
    LANGUAGE='en_US:en'

# Install ONLY runtime dependencies (NO dev packages)
# hadolint ignore=DL3018
RUN apk add --no-cache \
    libgcc=13.2.1_git20240309-r1 \
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
  chmod +x /module/scripts/utils/*.sh && \
  chmod 644 /module/scripts/*.py 2>/dev/null || true && \
  chmod 540 /deployments/run-java.sh && \
  chmod g+rwX /deployments

USER ci:ci
WORKDIR /module
