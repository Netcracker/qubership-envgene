FROM python:3.12-slim-bookworm

# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    vim \
 && rm -rf /var/lib/apt/lists/*

# sops
RUN curl -LO https://github.com/getsops/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 && \
    mv sops-v3.9.0.linux.amd64 /usr/local/bin/sops && \
    chmod +x /usr/local/bin/sops

# PyPI test dependencies only (repo packages are installed editable at container start via up.sh)
COPY devtools/cucumber/cucumber_requirements.txt /tmp/cucumber_requirements.txt
# hadolint ignore=DL3013,DL3042
RUN pip install --no-cache-dir "uv>=0.9.5" && \
    uv pip install --system --no-cache-dir -r /tmp/cucumber_requirements.txt
