# checkov:skip=CKV_DOCKER_3:This build container requires root privileges for CI/CD operations
# checkov:skip=CKV_DOCKER_8:Root required for workspace write (shutil.copy2 utime) in CI/CD
# checkov:skip=CKV2_DOCKER_1:sudo is required for certain operations in scripts

# Stage 1: Build Java JAR
FROM maven:3.9-eclipse-temurin-17 AS maven-build

COPY build_effective_set_generator /build_effective_set_generator
RUN mvn --batch-mode package -Dgpg.skip=true -f /build_effective_set_generator/pom.xml

# Stage 2: Build Python dependencies
FROM ghcr.io/netcracker/qubership-envgene-base-modules:1.0.0 AS build

ARG RUN_JAVA_VERSION=1.3.8

# hadolint ignore=DL3018
RUN apk add --no-cache \
    libffi-dev=3.4.4-r3 \
    openssl-dev=3.1.8-r1 \
    python3-dev=3.11.14-r0 \
    cargo=1.76.0-r0 \
    rust=1.76.0-r0 \
    build-base=0.5-r3

COPY build_envgene/build/pip.conf /etc/pip.conf
COPY build_envgene/build/requirements.txt /build/requirements.txt
COPY build_envgene/build/constraint.txt /build/constraint.txt

COPY python /python
COPY schemas /schemas
COPY scripts/ /module/scripts/
COPY build_envgene/scripts/ /module/scripts/

RUN pip install --no-cache-dir --retries 10 --timeout 60 \
    -r /build/requirements.txt \
    /python/envgene \
    /python/artifact-searcher

RUN mkdir -p /deployments && \
    curl -sSL https://repo1.maven.org/maven2/io/fabric8/run-java-sh/${RUN_JAVA_VERSION}/run-java-sh-${RUN_JAVA_VERSION}-sh.sh \
    -o /deployments/run-java.sh

COPY --from=maven-build /build_effective_set_generator/effective-set-generator/target/*.jar /deployments/app.jar

RUN rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyo' -delete && \
    find /module/venv/lib/python3.12/site-packages -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf /module/venv/lib/python3.12/site-packages/pytest* \
        /module/venv/lib/python3.12/site-packages/_pytest* 2>/dev/null || true && \
    /module/venv/bin/pip cache purge

RUN chmod 754 /module/scripts/*

# Stage 3: Runtime
FROM ghcr.io/netcracker/qubership-envgene-base-modules:1.0.0 AS runtime

ARG JAVA_PACKAGE=openjdk17-jre-headless=17.0.14_p7-r0

ENV LANG='en_US.UTF-8' \
    LANGUAGE='en_US:en' \
    PYTHONPATH='/module/scripts'

# hadolint ignore=DL3018
RUN apk add --no-cache \
    libgcc=13.2.1_git20231014-r0 \
    ${JAVA_PACKAGE}

COPY --from=build /module /module
COPY --from=build /schemas /schemas
COPY --from=build /python /python
COPY --from=build /etc/pip.conf /etc/pip.conf
COPY --from=build /deployments /deployments

RUN rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete && \
    /module/venv/bin/pip cache purge

RUN chown -R ci:ci /module /deployments && \
    chmod +x /module/scripts/*.sh && \
    chmod +x /module/scripts/utils/*.sh && \
    chmod 644 /module/scripts/*.py 2>/dev/null || true && \
    chmod 540 /deployments/run-java.sh && \
    chmod g+rwX /deployments

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# checkov:skip=CKV_DOCKER_8:Root required for workspace write in CI/CD
# hadolint ignore=DL3002
USER root
WORKDIR /module/scripts
CMD ["bash"]
