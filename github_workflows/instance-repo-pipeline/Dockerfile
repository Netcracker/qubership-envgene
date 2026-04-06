# syntax=docker/dockerfile:1
#-----------Stage 1-----------
FROM alpine:3.21 AS initial
WORKDIR /workspace

COPY github_workflows/instance-repo-pipeline/.github /opt/github

COPY github_workflows/instance-repo-pipeline/extend_logic/scripts/ /opt/github/scripts/

RUN find /opt/github/scripts -type f -name "*.sh" -exec chmod +x {} \;

#-----------Stage 2-----------
FROM alpine:3.21

LABEL org.opencontainers.image.description="Github Workflows - Envgene Instance pipeline"

RUN apk add --no-cache python3=3.12.12-r0 py3-pip=24.3.1-r0 git=2.47.3-r0 \
    && pip3 install --no-cache-dir --break-system-packages ruamel.yaml==0.18.6

COPY --from=initial /opt/github /opt/github

USER 1000
CMD ["sh", "-c", "sleep infinity"]
