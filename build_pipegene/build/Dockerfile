#########################################
# Stage 1: Build
# Multi-stage build to reduce final image size
FROM python:3.12-alpine3.19 AS build
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]

# Install build dependencies (pinned)
RUN set -eux; \
    apk update; \
    ver() { apk list --verbose --available "$1" | head -n1 | sed -E "s/^$1-//; s/ .*//"; }; \
    apk add --no-cache \
        gcc="$(ver gcc)" \
        musl-dev="$(ver musl-dev)" \
        libffi-dev="$(ver libffi-dev)" \
        openssl-dev="$(ver openssl-dev)" \
        git="$(ver git)" \
        curl="$(ver curl)" \
        jq="$(ver jq)" \
        yq="$(ver yq)" \
        gettext="$(ver gettext)" \
        sed="$(ver sed)" \
        age="$(ver age)"; \
    rm -rf /var/cache/apk/*

# Copy configuration files (merged into build directory)
COPY build_pipegene/build/sources.list /etc/apk/repositories
COPY build_pipegene/build/pip.conf /etc/pip.conf
COPY build_pipegene/build/constraint.txt /build/constraint.txt
COPY build_pipegene/build/requirements.txt /build/requirements.txt

# Copy source code
COPY python /python
COPY schemas /module/schemas
COPY base_modules/scripts /module/scripts
COPY build_pipegene/scripts /module/scripts
COPY scripts/utils /module/scripts/scripts/utils/
COPY build_pipegene/pipegene_plugins /module/scripts/pipegene_plugins

# Create virtual environment and install Python packages
RUN python -m venv /module/venv && \
    /module/venv/bin/pip install --upgrade pip setuptools wheel && \
    /module/venv/bin/pip install --no-cache-dir --retries 10 --timeout 60 -r /build/requirements.txt && \
    /module/venv/bin/pip install /python/integration /python/jschon-sort /python/envgene && \
    /module/venv/bin/pip install PyYAML

# Download and install SOPS for secrets management (use curl for BusyBox compatibility)
RUN curl --fail --show-error --location --retry 3 \
    https://github.com/mozilla/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 \
    -o /usr/local/bin/sops && \
    chmod +x /usr/local/bin/sops

# Aggressive cleanup to reduce image size
RUN apk del gcc musl-dev libffi-dev openssl-dev && \
    rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyo' -delete && \
    ( find /module/venv/lib/python3.12/site-packages -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true ) && \
    ( rm -rf /module/venv/lib/python3.12/site-packages/pytest* /module/venv/lib/python3.12/site-packages/_pytest* 2>/dev/null || true ) && \
    ( rm -rf /module/venv/lib/python3.12/site-packages/resources 2>/dev/null || true ) && \
    ( rm -rf /module/venv/lib/python3.12/site-packages/botocore 2>/dev/null || true ) && \
    ( rm -rf /module/venv/lib/python3.12/site-packages/boto3 2>/dev/null || true ) && \
    ( rm -rf /module/venv/lib/python3.12/site-packages/lxml 2>/dev/null || true ) && \
    ( rm -rf /module/venv/lib/python3.12/site-packages/diagrams 2>/dev/null || true ) && \
    ( /module/venv/bin/pip cache purge 2>/dev/null || true ) && \
    rm -rf /module/venv/lib/python3.12/site-packages/pip* 2>/dev/null || true

# Set permissions
RUN chmod 754 /module/scripts/*

#########################################
# Stage 2: Runtime
# Lightweight runtime image with only essential dependencies
FROM python:3.12-alpine3.19 AS runtime
SHELL ["/bin/ash", "-eo", "pipefail", "-c"]

# Install only essential runtime dependencies (pinned)
RUN set -eux; \
    apk update; \
    ver() { apk list --verbose --available "$1" | head -n1 | sed -E "s/^$1-//; s/ .*//"; }; \
    apk add --no-cache \
        bash="$(ver bash)" \
        ca-certificates="$(ver ca-certificates)" \
        curl="$(ver curl)" \
        jq="$(ver jq)" \
        yq="$(ver yq)" \
        gettext="$(ver gettext)" \
        sed="$(ver sed)" \
        age="$(ver age)" \
        git="$(ver git)"; \
    rm -rf /var/cache/apk/*

# Copy everything from build stage
COPY --from=build /module /module
COPY --from=build /usr/local/bin/sops /usr/local/bin/sops
COPY --from=build /python /python
COPY --from=build /etc/pip.conf /etc/pip.conf

# Set permissions
RUN chmod +x /usr/local/bin/sops

# Create directories that might be needed for CI environments
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
RUN set -eux; \
    rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache; \
    find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete; \
    /module/venv/bin/pip cache purge 2>/dev/null || true; \
    # Keep pip for runtime compatibility, but remove setuptools and wheel
    rm -rf /module/venv/lib/python3.12/site-packages/setuptools* /module/venv/lib/python3.12/site-packages/wheel* 2>/dev/null || true

# Set environment
ENV PATH=/module/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create user for security
RUN addgroup ci && adduser -D -h /module/ -s /bin/bash -G ci ci && \
    chown ci:ci -R /module

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

USER ci:ci
WORKDIR /module/scripts

# Default command
CMD ["bash"]
