# syntax=docker/dockerfile:1@sha256:ecfaec9ed6d810b56388c508f4121597bfbba70d41a6dfeee4d8cad5f295fc32
#-----------Stage 1-----------
FROM ghcr.io/netcracker/qubership-envgene-base-modules:1.0.2@sha256:70fb89ab2a333efbfee3fd1eae3e8a7c59f5245546d84a4bdd83ea707d32eec0 AS initial

WORKDIR /workspace

COPY github_workflows/instance-repo-pipeline/.github /opt/github

COPY github_workflows/instance-repo-pipeline/extend_logic/scripts/ /opt/github/extend_logic/scripts/

RUN find /opt/github/scripts -type f -name "*.sh" -exec chmod +x {} \; \
    && find /opt/github/extend_logic/scripts -type f -name "*.py" -exec chmod +x {} \;

#-----------Stage 2-----------
FROM ghcr.io/netcracker/qubership-envgene-base-modules:1.0.2@sha256:70fb89ab2a333efbfee3fd1eae3e8a7c59f5245546d84a4bdd83ea707d32eec0

LABEL org.opencontainers.image.description="Github Workflows - Envgene Instance pipeline"

COPY --from=initial /opt/github /opt/github

USER 1000
CMD ["sh", "-c", "sleep infinity"]
