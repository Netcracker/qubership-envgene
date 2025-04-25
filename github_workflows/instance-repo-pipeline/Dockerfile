#-----------Stage 1-----------
FROM alpine:3.19 AS initial
WORKDIR /workspace
COPY github_workflows/instance-repo-pipeline/.github /opt/github

#-----------Stage 2-----------
FROM scratch
COPY --from=initial /opt/github /opt/github
CMD ["sh", "-c", "sleep infinity"]