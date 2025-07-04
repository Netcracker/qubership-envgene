#########################################
## Stage 1: Builder
FROM mcr.microsoft.com/devcontainers/python:3.10-bullseye as builder

USER root

# Copy only files needed for installation first to leverage Docker cache
COPY requirements.txt /build/requirements.txt

# Install build dependencies and runtime packages in a single layer
RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    python3-cryptography \
    openssh-client \
    ca-certificates \
    coreutils \
    curl \
    sudo \
    zip \
    unzip \
    jq \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev &&\
    # Install sops
    curl --retry 3 --retry-connrefused --retry-delay 5 -LO https://github.com/mozilla/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 && \
    chmod +x sops-v3.9.0.linux.amd64 && \
    mv sops-v3.9.0.linux.amd64 /usr/local/bin/sops && \
    # Install Python packages
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /build/requirements.txt && \
    pip install --no-cache-dir PyYAML && \
    # Cleanup
    apt-get remove -y libxml2-dev libxslt1-dev zlib1g-dev build-essential && \
    apt-get autoremove -y && \
    rm -rf /tmp/* /var/tmp/* /root/.cache


WORKDIR /envgenehelper
