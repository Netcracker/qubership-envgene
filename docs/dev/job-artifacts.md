# Job Artifacts

## Overview

GitLab pipeline jobs pass state between each other through artifacts without repeated GIT checkouts. This document explains the mechanism and requirements.

Artifact size limit: **1500 MB**

## Git Checkout Strategy

### First Job in Pipeline

1. Performs `git checkout`
2. Gets fresh copy of repository
3. Modifies files (optional)
4. Saves required paths to job artifacts

### Intermediate Jobs

- Do NOT checkout repository
- Receive files from previous job's artifacts
- Modify files (optional)
- Save required paths to job artifacts

### git_commit_job

- Receives files from previous job's artifacts
- Does `git init` and `git pull` (retrieves current repository state from remote)
- Copies files from job's artifacts (overwrites pulled files with changes)
- Commits and pushes changes

## Required Artifact Paths

All jobs in the pipeline save **only** these paths to artifacts:

- `/environments/`
<!-- - `/environments/<cluster-name>/<env-name>`
- `/environments/<cluster-name>/cloud-passport`
- `/environments/<cluster-name>/parameters`
- `/environments/<cluster-name>/credentials`
- `/environments/<cluster-name>/resource_profiles`
- `/environments/<cluster-name>/shared_template_variables` -->
- `/configuration/`
- `/sboms/`
- `/templates/`

These paths are:

1. Modified by various jobs during pipeline execution
2. Needed by downstream jobs
3. Committed to GIT by `git_commit_job`
