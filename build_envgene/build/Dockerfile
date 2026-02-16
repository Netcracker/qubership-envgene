# checkov:skip=CKV_DOCKER_3:This build container requires root privileges for CI/CD operations
# checkov:skip=CKV2_DOCKER_1:sudo is required for certain operations in scripts

#########################################
# Stage 1: Build
#########################################
FROM ghcr.io/netcracker/qubership-envgene-base-modules:feature_add_all_deps AS base

# Add sudo for CI/CD operations
RUN apk add --no-cache sudo

# Copy configuration and source code
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
COPY scripts/build_template /build_env/scripts/build_template/
COPY scripts/cloud_passport/ /cloud_passport/scripts/
COPY schemas /build_env/schemas
COPY scripts/utils /module/scripts/utils

# Install envgene-specific Python packages
RUN /module/venv/bin/pip install --no-cache-dir --retries 10 --timeout 60 -r /build/requirements.txt && \
    /module/venv/bin/pip install /python/jschon-sort && \
    /module/venv/bin/pip install /python/envgene && \
    /module/venv/bin/pip install /python/integration && \
    /module/venv/bin/pip install /python/artifact-searcher && \
    /module/venv/bin/pip install --no-cache-dir --no-deps -r /build/creds_rotation_requirements.txt

# Cleanup to reduce image size
RUN apk del sudo 2>/dev/null || true && \
    rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyo' -delete && \
    find /module/venv/lib/python3.12/site-packages -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf /module/venv/lib/python3.12/site-packages/pytest* \
        /module/venv/lib/python3.12/site-packages/_pytest* 2>/dev/null || true && \
    /module/venv/bin/pip cache purge

RUN chmod 754 /module/scripts/* && \
    chmod 754 /module/creds_rotation_scripts/*

#########################################
# Stage 2: Runtime
#########################################
FROM ghcr.io/netcracker/qubership-envgene-base-modules:feature_add_all_deps AS runtime

# Add sudo for CI/CD operations
RUN apk add --no-cache sudo

# Copy envgene-specific artifacts from build
COPY --from=base /module /module
COPY --from=base /scripts/bg_manage /scripts/bg_manage
COPY --from=base /build_env /build_env
COPY --from=base /cloud_passport /cloud_passport
COPY --from=base /python /python
COPY --from=base /etc/pip.conf /etc/pip.conf

# Final cleanup
RUN rm -rf /var/cache/apk/* /tmp/* /var/tmp/* /root/.cache && \
    find /module/venv/lib/python3.12/site-packages -name '*.pyc' -delete && \
    /module/venv/bin/pip cache purge && \
    rm -rf /module/venv/lib/python3.12/site-packages/setuptools* \
        /module/venv/lib/python3.12/site-packages/wheel* 2>/dev/null || true

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

USER ci:ci
WORKDIR /module/scripts
CMD ["bash"]
