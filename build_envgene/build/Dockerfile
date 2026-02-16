# checkov:skip=CKV_DOCKER_3:This build container requires root privileges for CI/CD operations

FROM python:3.12-alpine3.19 AS build

# Install build dependencies
# checkov:skip=CKV2_DOCKER_1:sudo is required for certain operations in scripts
# hadolint ignore=DL3018
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    libxml2-dev \
    libxslt-dev \
    zlib-dev \
    git \
    curl \
    jq \
    openssh-client \
    sudo \
    zip \
    unzip

COPY build_envgene/build/pip.conf /etc/pip.conf
COPY build_envgene/build/requirements.txt /build/requirements.txt
COPY build_envgene/build/constraint.txt /build/constraint.txt
COPY creds_rotation/build/requirements.txt /build/creds_rotation_requirements.txt

COPY python /python
COPY build_envgene/scripts /module/scripts
COPY scripts/bg_manage /scripts/bg_manage
COPY creds_rotation/scripts /module/creds_rotation_scripts
COPY build_* create_* produce_* sort* /build_env/
COPY scripts/build_env /build_env/scripts/build_env/
COPY scripts/build_env/process_sd.py /module/scripts/
COPY scripts/build_template /build_env/scripts/build_template/
COPY scripts/cloud_passport/ /cloud_passport/scripts/
COPY schemas /build_env/schemas
COPY scripts/utils /module/scripts/utils

RUN python3 -m venv /module/venv && \
    /module/venv/bin/pip install --upgrade pip "setuptools<82" wheel

RUN /module/venv/bin/pip install --no-cache-dir --retries 10 --timeout 60 -r /build/requirements.txt

RUN /module/venv/bin/pip install /python/jschon-sort && \
    /module/venv/bin/pip install /python/envgene && \
    /module/venv/bin/pip install /python/integration && \
    /module/venv/bin/pip install /python/artifact-searcher && \
    /module/venv/bin/pip install --no-cache-dir --no-deps -r /build/creds_rotation_requirements.txt

RUN wget --quiet --tries=3 \
    https://github.com/mozilla/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 \
    -O /usr/local/bin/sops && \
    chmod +x /usr/local/bin/sops

# Aggressive cleanup to reduce image size
RUN apk del gcc musl-dev libffi-dev openssl-dev libxml2-dev libxslt-dev zlib-dev && \
    rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache
# Remove unnecessary files from Python packages
RUN find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete

RUN find /module/venv/lib/python3.12/site-packages -name '*.pyo' -delete
RUN find /module/venv/lib/python3.12/site-packages -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
RUN rm -rf /module/venv/lib/python3.12/site-packages/pytest* \
           /module/venv/lib/python3.12/site-packages/_pytest* 2>/dev/null || true
RUN /module/venv/bin/pip cache purge

RUN chmod 754 /module/scripts/* && \
    chmod 754 /module/creds_rotation_scripts/*


FROM python:3.12-alpine3.19 AS runtime

# Install only essential runtime dependencies
# checkov:skip=CKV2_DOCKER_1:sudo is required for certain operations in scripts
# hadolint ignore=DL3018
RUN apk add --no-cache \
    bash \
    ca-certificates \
    curl \
    jq \
    yq \
    gettext \
    age \
    git \
    openssh-client \
    sudo \
    zip \
    unzip \
    tar

COPY --from=build /module /module
COPY --from=build /scripts/bg_manage /scripts/bg_manage
COPY --from=build /usr/local/bin/sops /usr/local/bin/sops
COPY --from=build /build_env /build_env
COPY --from=build /cloud_passport /cloud_passport
COPY --from=build /python /python
COPY --from=build /etc/pip.conf /etc/pip.conf


# Create directories that might be needed for CI environments
# These directories are commonly used by GitHub Actions and GitLab CI
RUN mkdir -p /__w/_temp/_runner_file_commands && \
    mkdir -p /github/workspace && \
    mkdir -p /github/home && \
    mkdir -p /builds && \
    mkdir -p /cache && \
    chmod 777 /__w/_temp/_runner_file_commands && \
    chmod 777 /github/workspace && \
    chmod 777 /github/home && \
    chmod 777 /builds && \
    chmod 777 /cache

# Final cleanup
RUN rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache
RUN find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete
RUN /module/venv/bin/pip cache purge

ENV PATH=/module/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

CMD ["bash"]
