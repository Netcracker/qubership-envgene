#-----------Stage 1-----------
FROM alpine:3.19 AS initial
WORKDIR /workspace
COPY github_workflows/instance-repo-pipeline/.github /opt/github
RUN find /opt/github -type d -exec chmod 755 {} + && \
    find /opt/github -type f -exec chmod 644 {} +

#-----------Stage 2-----------
FROM alpine:3.19

ARG RUN_UID=1001
ARG RUN_GID=121

COPY --from=initial /opt/github /opt/github

RUN addgroup -S -g ${RUN_GID} ci \
    && adduser  -S -D -h /home/ci -u ${RUN_UID} -G ci ci \
    && chown -R ${RUN_UID}:${RUN_GID} /home/ci

USER ci:ci
CMD ["sh", "-c", "sleep infinity"]