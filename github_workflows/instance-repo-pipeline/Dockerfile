#-----------Stage 1-----------
FROM alpine:3.19 AS initial
WORKDIR /workspace
COPY github_workflows/instance-repo-pipeline/.github /opt/github

# Make all shell scripts executable
RUN find /opt/github/scripts -type f -name "*.sh" -exec chmod +x {} \;

#-----------Stage 2-----------
FROM scratch
COPY --from=initial /opt/github /opt/github
USER 1000
CMD ["sh", "-c", "sleep infinity"]