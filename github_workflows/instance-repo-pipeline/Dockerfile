# syntax=docker/dockerfile:1
#-----------Stage 1-----------
FROM alpine:3.23 AS initial
WORKDIR /workspace

COPY github_workflows/instance-repo-pipeline/.github /opt/github

RUN find /opt/github/scripts -type f -name "*.sh" -exec chmod +x {} \;

#-----------Stage 2-----------
FROM alpine:3.23

LABEL org.opencontainers.image.description="Github Workflows - Envgene Instance pipeline"

RUN apk add --no-cache python3=3.12.13-r0 py3-pip=25.1.1-r1 git=2.52.0-r0 \
    && pip3 install --no-cache-dir --break-system-packages ruamel.yaml==0.18.6

COPY --from=initial /opt/github /opt/github

USER 1000
CMD ["sh", "-c", "sleep infinity"]
