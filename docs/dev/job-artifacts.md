# Job Artifacts

## Overview

GitLab pipeline jobs pass state between each other through artifacts without repeated Git checkouts. This document explains the mechanism and requirements.

Artifact size limit: **1500 MB**

## Git Checkout Strategy

### First Job in Pipeline

1. Sets `GIT_STRATEGY: empty` so GitLab Runner skips the default clone
2. Runs sparse checkout as the first script step in the job container, pulling only the paths required for the target environment
3. Gets a filtered copy of the repository on disk
4. Modifies files (optional)
5. Saves required paths to job artifacts

Sparse checkout paths are computed by `get_sparse_checkout_paths()` in
[`build_pipegene/scripts/pipeline_helper.py`](/build_pipegene/scripts/pipeline_helper.py). The include list is
`REPO_ROOT_PATHS` plus the same environment paths used for job artifacts (`get_env_artifact_paths()`).
When `CRED_ROTATION_PAYLOAD` is set, checkout also includes all of `environments/<cluster-name>/` so credential
rotation can scan sibling environments in the same cluster.

### Intermediate Jobs

- Do NOT checkout repository (`GIT_STRATEGY: empty`)
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
- `/configuration/`
- `/sboms/`
- `/templates/`

These paths are:

1. Modified by various jobs during pipeline execution
2. Needed by downstream jobs
3. Committed to Git by `git_commit_job`

Shared directories under `environments/` that are included in both sparse checkout and artifacts are defined in `get_shared_entity_paths()` in
[`build_pipegene/scripts/pipeline_helper.py`](/build_pipegene/scripts/pipeline_helper.py).
