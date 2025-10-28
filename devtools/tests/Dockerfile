FROM python:3.12-slim-bookworm

RUN useradd -m appuser
USER appuser

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential=12.9 \
    curl=7.88.1-10+deb12u8 \
 && rm -rf /var/lib/apt/lists/*

# sops
RUN curl -LO https://github.com/getsops/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64 && \
    mv sops-v3.9.0.linux.amd64 /usr/local/bin/sops && \
    chmod +x /usr/local/bin/sops

# Optional pip.conf / sources.list
COPY dependencies/pip.conf /etc/pip.conf
COPY dependencies/sources.list /etc/apt/sources.list

# Copy dependencies and install them
COPY dependencies/tests_requirements.txt /tmp/
RUN pip install --no-cache-dir "uv>=0.9.5" && uv pip install --system --no-cache-dir -r /tmp/tests_requirements.txt

