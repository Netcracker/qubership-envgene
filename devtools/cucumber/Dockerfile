# checkov:skip=CKV_DOCKER_7:Base image is built dynamically
# checkov:skip=CKV_DOCKER_2:Healthcheck is not needed for test runner container
# hadolint ignore=DL3006
FROM local-envgene-main

# checkov:skip=CKV_DOCKER_8:Root required for workspace write in CI/CD
# hadolint ignore=DL3002
USER root

# hadolint ignore=DL3018
RUN apk add --no-cache curl && \
    curl -LO https://github.com/getsops/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 && \
    mv sops-v3.9.0.linux.amd64 /usr/local/bin/sops && \
    chmod +x /usr/local/bin/sops

# Optional pip.conf
COPY dependencies/pip.conf /etc/pip.conf

# PyPI test dependencies only
COPY dependencies/tests_requirements.txt /tmp/tests_requirements.txt

# The main image uses a virtual environment at /module/venv
# We install the test dependencies into the same environment
RUN /module/venv/bin/pip install --no-cache-dir "uv>=0.9.5" && \
    /module/venv/bin/uv pip install --python /module/venv --upgrade pip "setuptools<82" wheel && \
    /module/venv/bin/uv pip install --python /module/venv --no-cache-dir -r /tmp/tests_requirements.txt

ENV PATH="/module/venv/bin:${PATH}"
WORKDIR /workspace
