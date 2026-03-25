# ═══════════════════════════════════════════════════════════════════════════════════
# Stage 1: Build
# ═══════════════════════════════════════════════════════════════════════════════════
FROM ghcr.io/netcracker/qubership-envgene-base-modules:1.0.0 AS build

# Copy configuration files and source code
COPY build_pipegene/build/pip.conf /etc/pip.conf
COPY build_pipegene/build/constraint.txt /build/constraint.txt
COPY build_pipegene/build/requirements.txt /build/requirements.txt

COPY python /python
COPY schemas /module/schemas
COPY base_modules/scripts /module/scripts
COPY build_pipegene/scripts /module/scripts
COPY scripts/utils /module/scripts/scripts/utils/
COPY build_pipegene/pipegene_plugins /module/scripts/pipegene_plugins

# Create virtual environment and install Python packages
RUN pip install --no-cache-dir --retries 10 --timeout 60 \
    -r /build/requirements.txt \
    /python/integration \
    /python/jschon-sort \
    /python/envgene

# Cleanup to reduce image size
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

RUN chmod 754 /module/scripts/*

# ═══════════════════════════════════════════════════════════════════════════════════
# Stage 2: Runtime
# ═══════════════════════════════════════════════════════════════════════════════════
FROM ghcr.io/netcracker/qubership-envgene-base-modules:1.0.0 AS runtime

COPY --from=build /module /module
COPY --from=build /python /python
COPY --from=build /etc/pip.conf /etc/pip.conf

# Final cleanup
RUN set -eux; \
    rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache; \
    find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete; \
    /module/venv/bin/pip cache purge 2>/dev/null || true;

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

RUN chown -R ci:ci /module
USER ci:ci
WORKDIR /module/scripts
CMD ["bash"]
