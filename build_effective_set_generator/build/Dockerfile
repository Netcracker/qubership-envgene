#########################################
# Stage 1: Build (envgene-specific layer)
#########################################
FROM ghcr.io/netcracker/qubership-envgene-base-modules:feature_add_all_deps AS base

ARG RUN_JAVA_VERSION=1.3.8
# Add build deps for artifact-searcher (Rust/cargo) and cryptography (compile from source)
# hadolint ignore=DL3018
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    python3-dev \
    cargo \
    rust \
    build-base

# Copy envgene-specific sources
COPY python /python
COPY build_effective_set_generator/build/requirements.txt /build/requirements.txt
COPY build_effective_set_generator/build/pip.conf /etc/pip.conf

# Install envgene-specific Python packages (with source build for cryptography)
RUN /module/venv/bin/pip install --no-cache-dir \
    --no-binary cffi \
    --no-binary cryptography \
    -r /build/requirements.txt && \
    /module/venv/bin/pip install --no-cache-dir \
    /python/integration \
    /python/jschon-sort \
    /python/envgene \
    /python/artifact-searcher

# Download run-java and copy JAR
RUN mkdir -p /deployments && \
    curl -sSL "https://repo1.maven.org/maven2/io/fabric8/run-java-sh/${RUN_JAVA_VERSION}/run-java-sh-${RUN_JAVA_VERSION}-sh.sh" \
    -o /deployments/run-java.sh

COPY build_effective_set_generator/effective-set-generator/target/*.jar /deployments/app.jar

#########################################
# Stage 2: Runtime
#########################################
FROM ghcr.io/netcracker/qubership-envgene-base-modules:feature_add_all_deps AS runtime
ARG JAVA_PACKAGE=openjdk17-jre-headless

ENV LANG='en_US.UTF-8' \
    LANGUAGE='en_US:en'

# Add Java runtime (effective_set-specific)
# hadolint ignore=DL3018
RUN apk add --no-cache \
    libffi \
    libgcc \
    ${JAVA_PACKAGE}

# Copy envgene-specific artifacts from build
COPY --from=base /python /python
COPY --from=base /module/venv /module/venv
COPY --from=base /deployments /deployments

# Copy envgene-specific scripts (overlay on base scripts)
COPY scripts/build_env/ /build_env/scripts/build_env/
COPY scripts/build_env/process_sd.py /module/scripts/
COPY build_effective_set_generator/scripts/ /module/scripts/
COPY scripts/utils/ /module/scripts/utils/
COPY build_envgene/scripts/handle_certs.sh /module/scripts/

# Permissions
RUN chown -R ci:ci /module /deployments && \
    chmod +x /module/scripts/*.sh && \
    chmod 644 /module/scripts/*.py 2>/dev/null || true && \
    chmod 540 /deployments/run-java.sh && \
    chmod g+rwX /deployments

USER ci:ci
WORKDIR /module
