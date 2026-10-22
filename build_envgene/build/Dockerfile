# checkov:skip=CKV_DOCKER_3:This build container requires root privileges for CI/CD operations
# checkov:skip=CKV_DOCKER_8:Root required for workspace write (shutil.copy2 utime) in CI/CD
# checkov:skip=CKV2_DOCKER_1:sudo is required for certain operations in scripts

# Stage 0: Build static native effective set generator
FROM quay.io/quarkus/ubi-quarkus-mandrel-builder-image:jdk-17 AS java-native-builder

ARG MUSL_VERSION=1.2.5
ARG ZLIB_VERSION=1.3.1

ENV MUSL_HOME=/home/quarkus/musl
ENV PATH="${MUSL_HOME}/bin:${PATH}"

RUN curl -sSLf "https://musl.libc.org/releases/musl-${MUSL_VERSION}.tar.gz" | tar xz -C /tmp && \
    cd "/tmp/musl-${MUSL_VERSION}" && \
    ./configure --prefix="${MUSL_HOME}" --disable-shared && \
    make -j"$(nproc)" install && \
    ln -s "${MUSL_HOME}/bin/musl-gcc" "${MUSL_HOME}/bin/x86_64-linux-musl-gcc" && \
    curl -sSLf "https://zlib.net/fossils/zlib-${ZLIB_VERSION}.tar.gz" | tar xz -C /tmp && \
    cd "/tmp/zlib-${ZLIB_VERSION}" && \
    CC=musl-gcc ./configure --prefix="${MUSL_HOME}" --static && \
    make -j"$(nproc)" install

WORKDIR /project

COPY --chown=quarkus:quarkus build_effective_set_generator /project

RUN chmod +x mvnw && ./mvnw --batch-mode package -pl effective-set-generator -am -Dnative -DskipTests -Dgpg.skip=true

# Stage 1: Build Python dependencies
FROM ghcr.io/netcracker/qubership-envgene-base-modules:fix_slim-base-image AS build

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

ENV PATH="/module/venv/bin:${PATH}"

RUN python3 -m venv /module/venv && \
    pip install --no-cache-dir pip==26.0.1

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

RUN rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyo' -delete && \
    find /module/venv/lib/python3.12/site-packages -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf /module/venv/lib/python3.12/site-packages/pytest* \
        /module/venv/lib/python3.12/site-packages/_pytest* 2>/dev/null || true && \
    /module/venv/bin/pip uninstall -y setuptools pip

RUN rm -rf /module/scripts/tests && \
    find /module/venv/lib/python3.12/site-packages/botocore/data -mindepth 1 -maxdepth 1 -type d \
    ! -name codeartifact ! -name ecr ! -name secretsmanager ! -name sts ! -name sso ! -name sso-oidc \
    -exec rm -rf {} + && \
    /module/venv/bin/python -m compileall -q -j 0 --invalidation-mode unchecked-hash \
    /module/venv/lib/python3.12/site-packages /module/scripts && \
    chmod 754 /module/scripts/* && \
    chmod +x /module/scripts/utils/*.sh

# Stage 2: Runtime
FROM ghcr.io/netcracker/qubership-envgene-base-modules:fix_slim-base-image AS runtime

ENV LANG='en_US.UTF-8' \
    LANGUAGE='en_US:en' \
    PYTHONPATH='/module/scripts' \
    PATH="/module/venv/bin:${PATH}"

COPY --from=build --chown=ci:ci /module /module
COPY --from=build /schemas /schemas
COPY --from=java-native-builder --chown=ci:ci --chmod=755 /project/effective-set-generator/target/*-runner /deployments/envgene-es

# checkov:skip=CKV_DOCKER_8:Root required for workspace write in CI/CD
# hadolint ignore=DL3002
USER root
WORKDIR /module/scripts
CMD ["bash"]
