#-----------Stage 1-----------
FROM alpine:3.19 AS initial
WORKDIR /workspace
COPY github_workflows/instance-repo-pipeline/.github /opt/github

#-----------Stage 2-----------
FROM alpine:3.19
COPY --from=initial /opt/github /opt/github
# create and use non-root user
RUN addgroup -S ci && adduser -S ci -G ci
USER ci:ci
CMD ["sh", "-c", "sleep infinity"]