#########################################
# Stage 1: Build
# Multi-stage build to reduce final image size
FROM python:3.12-alpine3.19 AS build

# Install build dependencies
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
    zip \
    unzip

# Copy configuration files
COPY build_envgene/build/pip.conf /etc/pip.conf
COPY build_envgene/build/requirements.txt /build/requirements.txt
COPY build_envgene/build/requirements.yml /build/requirements.yml
COPY build_envgene/build/constraint.txt /build/constraint.txt
COPY creds_rotation/build/requirements.txt /build/creds_rotation_requirements.txt

# Copy source code
COPY python /python
COPY build_envgene/ansible /module/ansible
COPY build_envgene/scripts /module/scripts
COPY creds_rotation/scripts /module/creds_rotation_scripts
COPY build_* create_* produce_* sort* /build_env/
COPY scripts /build_env/scripts
COPY env-builder /build_env/env-builder
COPY schemas /build_env/schemas

ENV ANSIBLE_LIBRARY=/module/ansible/library

# Create virtual environment and install Python packages
RUN python -m venv /module/venv && \
    /module/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /module/venv/bin/pip install --no-cache-dir --retries 10 --timeout 60 -r /build/requirements.txt && \
    /module/venv/bin/pip install --no-cache-dir --upgrade ansible-core && \
    /module/venv/bin/ansible-galaxy collection install -p /module/ansible/collections ansible.utils ansible.posix community.general && \
    /module/venv/bin/pip install /python/jschon-sort /python/envgene /python/integration && \
    /module/venv/bin/pip install --no-cache-dir --no-deps -r /build/creds_rotation_requirements.txt

# Download and install SOPS for secrets management (use curl for BusyBox compatibility)
RUN curl --fail --show-error --location --retry 3 \
    https://github.com/mozilla/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 \
    -o /usr/local/bin/sops && \
    chmod +x /usr/local/bin/sops

# Aggressive cleanup to reduce image size
RUN apk del gcc musl-dev libffi-dev openssl-dev libxml2-dev libxslt-dev zlib-dev && \
    rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyo' -delete && \
    find /module/venv/lib/python3.12/site-packages -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true && \
    # Remove heavy, unused Ansible collections
    rm -rf /module/ansible/collections/ansible_collections/amazon \
           /module/ansible/collections/ansible_collections/azure \
           /module/ansible/collections/ansible_collections/google \
           /module/ansible/collections/ansible_collections/kubernetes 2>/dev/null || true && \
    # Remove pytest from venv
    rm -rf /module/venv/lib/python3.12/site-packages/pytest* /module/venv/lib/python3.12/site-packages/_pytest* 2>/dev/null || true && \
    /module/venv/bin/python -m pip cache purge && \
    # Remove Ansible/galaxy caches if any
    rm -rf /root/.ansible

# Set permissions
RUN find /module -type d -exec chmod 755 {} + && \
    find /module -type f -exec chmod 644 {} + && \
    chmod -R 755 /module/scripts /module/creds_rotation_scripts

#########################################
# Stage 2: Runtime
# Lightweight runtime image with only essential dependencies
FROM python:3.12-alpine3.19 AS runtime

# Install only essential runtime dependencies
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
    zip \
    unzip

# Copy everything from build stage
COPY --from=build /module /module
COPY --from=build /usr/local/bin/sops /usr/local/bin/sops
COPY --from=build /build_env /build_env

# Set permissions
RUN chmod +x /usr/local/bin/sops && \
    chmod -R 755 /module/venv/bin || true

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
RUN rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete && \
    /module/venv/bin/pip cache purge 2>/dev/null || true && \
    # Keep pip for runtime compatibility, but remove setuptools and wheel
    rm -rf /module/venv/lib/python3.12/site-packages/setuptools* /module/venv/lib/python3.12/site-packages/wheel* 2>/dev/null || true

ARG RUN_UID=1001
ARG RUN_GID=121

# Create and configure non-root user then remove shadow to save space
RUN set -eux; \
    apk add --no-cache shadow; \
    if getent group ci >/dev/null 2>&1; then \
        groupmod -o -g ${RUN_GID} ci || true; \
    else \
        addgroup -S -g ${RUN_GID} ci; \
    fi; \
    if id -u ci >/dev/null 2>&1; then \
        usermod -o -u ${RUN_UID} -g ${RUN_GID} -d /home/ci -m ci || true; \
    else \
        adduser -S -D -h /home/ci -u ${RUN_UID} -G ci ci; \
    fi; \
    mkdir -p /home/ci && chown -R ${RUN_UID}:${RUN_GID} /home/ci /module /build_env || true; \
    apk del shadow; \
    rm -rf /root/.ansible /home/ci/.ansible

# Set environment
ENV PATH=/module/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ANSIBLE_LIBRARY=/module/ansible/library \
    ANSIBLE_COLLECTIONS_PATH=/module/ansible/collections

# Create and use non-root user for runtime
USER ci:ci
# Set working directory for runtime
WORKDIR /module/ansible

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command
CMD ["bash"]
