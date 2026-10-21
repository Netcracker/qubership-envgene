# checkov:skip=CKV_DOCKER_3:This build container requires root privileges for CI/CD operations
# checkov:skip=CKV_DOCKER_8:Root required for workspace write (shutil.copy2 utime) in CI/CD
# checkov:skip=CKV2_DOCKER_1:sudo is required for certain operations in scripts

# Stage 0: Build Native Java CLI Binary
FROM quay.io/quarkus/ubi-quarkus-mandrel-builder-image:jdk-17 AS java-native-builder

WORKDIR /project

COPY --chown=quarkus:quarkus build_effective_set_generator /project

RUN chmod +x mvnw && ./mvnw --batch-mode package -pl :vals-reference-cli -am -Dnative

# Stage 1: Build Java JAR
FROM maven:3.9-eclipse-temurin-17 AS maven-build

COPY build_effective_set_generator /build_effective_set_generator
RUN mvn --batch-mode package -Dgpg.skip=true -pl effective-set-generator -am -f /build_effective_set_generator/pom.xml

# Stage 2: Build minimal JRE
FROM ghcr.io/netcracker/qubership-envgene-base-modules:fix_slim-base-image AS jre-build

ARG JDK_VERSION=17.0.20_p8-r0

# hadolint ignore=DL3018
RUN apk add --no-cache \
    "openjdk17-jdk=${JDK_VERSION}" \
    "openjdk17-jmods=${JDK_VERSION}" \
    'binutils=2.45.1-r0'

COPY --from=maven-build /build_effective_set_generator/effective-set-generator/target/*.jar /deployments/app.jar

RUN zip -qd /deployments/app.jar 'licenses/*' && \
    JDK=/usr/lib/jvm/java-17-openjdk && \
    "$JDK/bin/jlink" \
    --add-modules "$("$JDK/bin/jdeps" --ignore-missing-deps --print-module-deps --multi-release 17 /deployments/app.jar),jdk.zipfs,jdk.crypto.ec" \
    --strip-debug --no-man-pages --no-header-files --compress=2 \
    --output /opt/jre && \
    /opt/jre/bin/java -Xshare:dump && \
    /opt/jre/bin/java -XX:ArchiveClassesAtExit=/deployments/app.jsa -jar /deployments/app.jar --help

# Stage 3: Build Python dependencies
FROM ghcr.io/netcracker/qubership-envgene-base-modules:fix_slim-base-image AS build

ARG RUN_JAVA_VERSION=1.3.8

# hadolint ignore=DL3018
RUN apk add --no-cache \
    'libffi-dev=3.5.2-r0' \
    'openssl-dev=3.5.9-r0' \
    'python3-dev=3.12.15-r0' \
    'cargo=1.91.1-r2' \
    'rust=1.91.1-r2' \
    'build-base=0.5-r3'

COPY build_envgene/build/pip.conf /etc/pip.conf
COPY build_envgene/build/requirements.txt /build/requirements.txt
COPY build_envgene/build/constraint.txt /build/constraint.txt

COPY modules /modules
COPY schemas /schemas
COPY scripts/ /module/scripts/


RUN pip install --no-cache-dir --retries 10 --timeout 60 \
    -r /build/requirements.txt \
    /modules/envgene \
    /modules/artifact-searcher \
    /modules/external-cred-provision \
    /modules/dpg \
    /modules/sbom_generator \
    /modules/envgene-shared && \
    pip uninstall -y \
    kubernetes durationpy websocket-client oauthlib requests-oauthlib \
    minio pycryptodome argon2-cffi argon2-cffi-bindings \
    python-gitlab requests-toolbelt \
    ghapi fastcore \
    python-jenkins pbr multi-key-dict \
    webexpythonsdk \
    http-exceptions

RUN mkdir -p /deployments && \
    curl -sSL https://repo1.maven.org/maven2/io/fabric8/run-java-sh/${RUN_JAVA_VERSION}/run-java-sh-${RUN_JAVA_VERSION}-sh.sh \
    -o /deployments/run-java.sh

COPY --from=jre-build /deployments/app.jar /deployments/app.jsa /deployments/

RUN rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyo' -delete && \
    find /module/venv/lib/python3.12/site-packages -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf /module/venv/lib/python3.12/site-packages/pytest* \
        /module/venv/lib/python3.12/site-packages/_pytest* 2>/dev/null || true && \
    /module/venv/bin/pip cache purge

RUN rm -rf /module/scripts/tests && \
    find /module/venv/lib/python3.12/site-packages/botocore/data -mindepth 1 -maxdepth 1 -type d \
    ! -name codeartifact ! -name ecr ! -name secretsmanager ! -name sts ! -name sso ! -name sso-oidc \
    -exec rm -rf {} + && \
    /module/venv/bin/python -m compileall -q -j 0 --invalidation-mode unchecked-hash \
    /module/venv/lib/python3.12/site-packages /module/scripts && \
    chmod 754 /module/scripts/* && \
    chmod +x /module/scripts/utils/*.sh && \
    chmod 540 /deployments/run-java.sh && \
    chmod g+rwX /deployments

# Stage 4: Runtime
FROM ghcr.io/netcracker/qubership-envgene-base-modules:fix_slim-base-image AS runtime

ENV LANG='en_US.UTF-8' \
    LANGUAGE='en_US:en' \
    PYTHONPATH='/module/scripts' \
    JAVA_HOME='/opt/jre' \
    PATH="/opt/jre/bin:${PATH}"

# hadolint ignore=DL3018
RUN apk add --no-cache \
    libgcc=15.2.0-r2

COPY --from=jre-build /opt/jre /opt/jre
COPY --from=build --chown=ci:ci /module /module
COPY --from=build /schemas /schemas
COPY --from=build /etc/pip.conf /etc/pip.conf
COPY --from=build --chown=ci:ci /deployments /deployments
COPY --from=java-native-builder --chown=ci:ci --chmod=755 /project/vals-reference-cli/target/*-runner /module/scripts/vals-reference-cli

# checkov:skip=CKV_DOCKER_8:Root required for workspace write in CI/CD
# hadolint ignore=DL3002
USER root
WORKDIR /module/scripts
CMD ["bash"]
