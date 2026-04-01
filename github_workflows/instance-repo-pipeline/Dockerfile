#-----------Stage 1-----------
FROM python:3.12-alpine3.19 AS initial
WORKDIR /workspace
COPY github_workflows/instance-repo-pipeline/.github /opt/github

# Make all shell scripts executable
RUN find /opt/github/scripts -type f -name "*.sh" -exec chmod +x {} \;

#-----------Stage 2-----------
FROM python:3.12-alpine3.19
RUN pip install --no-cache-dir ruamel.yaml==0.18.5
COPY --from=initial /opt/github /opt/github
USER 1000
CMD ["sh", "-c", "sleep infinity"]