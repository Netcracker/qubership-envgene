# syntax=docker/dockerfile:1
#-----------Stage 1-----------
FROM alpine:3.19 AS initial
WORKDIR /workspace

COPY github_workflows/instance-repo-pipeline/.github /opt/github

RUN find /opt/github/scripts -type f -name "*.sh" -exec chmod +x {} \;

#-----------Stage 2-----------
FROM alpine:3.19

LABEL org.opencontainers.image.description="Github Workflows - Envgene Instance pipeline"

RUN apk add --no-cache python3 py3-pip git \
    && pip3 install --no-cache-dir ruamel.yaml==0.18.6

COPY --from=initial /opt/github /opt/github

USER 1000
CMD ["sh", "-c", "sleep infinity"]
    