# checkov:skip=CKV_DOCKER_3:This build container requires root privileges for CI/CD operations

#########################################
# Stage 1: Build
# Multi-stage build to reduce final image size
FROM python:3.12-alpine3.19 AS build

# Install build dependencies
# checkov:skip=CKV2_DOCKER_1:sudo is required for certain operations in scripts
# hadolint ignore=DL3018
# hadolint ignore=DL3059
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
COPY scripts/build_env /build_env/scripts/build_env/
COPY scripts/build_template /build_env/scripts/build_template/
COPY scripts/cloud_passport/ /cloud_passport/scripts/
COPY schemas /build_env/schemas
COPY scripts/utils /module/scripts/utils

ENV ANSIBLE_LIBRARY=/module/ansible/library

# Create virtual environment and install Python packages
RUN python -m venv /module/venv
RUN /module/venv/bin/pip install --upgrade pip setuptools wheel
RUN /module/venv/bin/pip install --no-cache-dir --retries 10 --timeout 60 -r /build/requirements.txt
# Install essential Ansible collections
# Install to virtual environment site-packages for Python module access
RUN /module/venv/bin/ansible-galaxy collection install ansible.utils -p /module/venv/lib/python3.12/site-packages/ansible_collections
RUN /module/venv/bin/ansible-galaxy collection install ansible.posix -p /module/venv/lib/python3.12/site-packages/ansible_collections
RUN /module/venv/bin/ansible-galaxy collection install community.general -p /module/venv/lib/python3.12/site-packages/ansible_collections
# Also install to custom location for playbook usage
RUN /module/venv/bin/ansible-galaxy collection install ansible.utils -p /module/ansible/collections
RUN /module/venv/bin/ansible-galaxy collection install ansible.posix -p /module/ansible/collections
RUN /module/venv/bin/ansible-galaxy collection install community.general -p /module/ansible/collections

RUN /module/venv/bin/pip install /python/jschon-sort
RUN /module/venv/bin/pip install /python/envgene
RUN /module/venv/bin/pip install /python/integration
RUN /module/venv/bin/pip install /python/artifact-searcher
RUN /module/venv/bin/pip install --no-cache-dir --no-deps -r /build/creds_rotation_requirements.txt

# Download and install SOPS for secrets management
RUN wget --tries=3 \
    https://github.com/mozilla/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 \
    -O /usr/local/bin/sops && \
    chmod +x /usr/local/bin/sops

# Aggressive cleanup to reduce image size
RUN apk del gcc musl-dev libffi-dev openssl-dev libxml2-dev libxslt-dev zlib-dev
RUN rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache
# Remove unnecessary files from Python packages
RUN find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete
# Don't remove test directories as they might be needed by Ansible
RUN find /module/venv/lib/python3.12/site-packages -name '*.pyo' -delete
RUN find /module/venv/lib/python3.12/site-packages -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
# Remove heavy Ansible collections that are not essential (but keep ansible.posix and ansible.utils)
RUN rm -rf /module/venv/lib/python3.12/site-packages/ansible_collections/amazon /module/venv/lib/python3.12/site-packages/ansible_collections/azure /module/venv/lib/python3.12/site-packages/ansible_collections/google /module/venv/lib/python3.12/site-packages/ansible_collections/kubernetes 2>/dev/null || true
# Remove test packages that are not needed in runtime (but keep Ansible test files)
RUN rm -rf /module/venv/lib/python3.12/site-packages/pytest* /module/venv/lib/python3.12/site-packages/_pytest* 2>/dev/null || true
RUN /module/venv/bin/pip cache purge

# Verify collections are still accessible after cleanup
RUN /module/venv/bin/python -c "import ansible_collections.ansible.posix; print('ansible.posix collection still accessible after cleanup')"

# Set permissions
RUN chmod 754 /module/scripts/*
RUN chmod 754 /module/creds_rotation_scripts/*

#########################################
# Stage 2: Runtime
# Lightweight runtime image with only essential dependencies
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

# Copy everything from build stage
COPY --from=build /module /module
COPY --from=build /usr/local/bin/sops /usr/local/bin/sops
COPY --from=build /build_env /build_env
COPY --from=build /cloud_passport /cloud_passport
COPY --from=build /python /python
COPY --from=build /etc/pip.conf /etc/pip.conf

# Verify collections are accessible in runtime stage
RUN /module/venv/bin/python -c "import ansible_collections.ansible.posix; print('ansible.posix collection accessible in runtime')"

# Set permissions
RUN chmod +x /usr/local/bin/sops

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
# Don't remove test directories as they might be needed by Ansible
RUN /module/venv/bin/pip cache purge
# Keep pip for runtime compatibility, but remove setuptools and wheel
RUN rm -rf /module/venv/lib/python3.12/site-packages/setuptools* /module/venv/lib/python3.12/site-packages/wheel* 2>/dev/null || true

# Set environment
ENV PATH=/module/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ANSIBLE_LIBRARY=/module/ansible/library \
    ANSIBLE_COLLECTIONS_PATH=/module/venv/lib/python3.12/site-packages/ansible_collections:/module/ansible/collections

# Simple root-based container for CI/CD environments
# This container runs as root to avoid permission issues in CI/CD pipelines
WORKDIR /module/ansible

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command
CMD ["bash"]
