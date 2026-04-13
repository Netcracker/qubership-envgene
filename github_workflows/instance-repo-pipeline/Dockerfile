# syntax=docker/dockerfile:1
#-----------Stage 1-----------
FROM ghcr.io/netcracker/qubership-envgene-base-modules:feature_add_ruamel AS initial

WORKDIR /workspace

COPY github_workflows/instance-repo-pipeline/.github /opt/github

COPY github_workflows/instance-repo-pipeline/extend_logic/scripts/ /opt/github/extend_logic/scripts/

RUN find /opt/github/scripts -type f -name "*.sh" -exec chmod +x {} \; \
    && find /opt/github/extend_logic/scripts -type f -name "*.py" -exec chmod +x {} \;

#-----------Stage 2-----------
FROM ghcr.io/netcracker/qubership-envgene-base-modules:feature_add_ruamel

LABEL org.opencontainers.image.description="Github Workflows - Envgene Instance pipeline"

COPY --from=initial /opt/github /opt/github

USER 1000
CMD ["sh", "-c", "sleep infinity"]
