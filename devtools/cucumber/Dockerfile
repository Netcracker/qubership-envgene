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

# PyPI test dependencies only
COPY devtools/cucumber/cucumber_requirements.txt /tmp/cucumber_requirements.txt

# The main image uses a virtual environment at /module/venv
# We install the test dependencies into the same environment
COPY --from=ghcr.io/astral-sh/uv:0.12.24 /uv /usr/local/bin/uv

RUN uv pip install --python /module/venv --no-cache-dir pip==26.0.1 -r /tmp/cucumber_requirements.txt

ENV PATH="/module/venv/bin:${PATH}"
WORKDIR /workspace
