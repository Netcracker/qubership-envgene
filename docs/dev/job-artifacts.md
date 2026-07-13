# Job Artifacts

## Overview

GitLab pipeline jobs pass state between each other through artifacts without repeated Git checkouts. This document explains the mechanism and requirements.

Artifact size limit: **1500 MB**

## Git Checkout Strategy

### First Job in Pipeline

1. Sets `GIT_STRATEGY: empty` so GitLab Runner skips the default clone
2. Runs sparse checkout as the first script
3. Gets a filtered copy of the repository on disk
4. Saves required paths and the `.git` directory to job artifacts

The sparse checkout path list is built from three groups:

**Repository root directories** (always included):

- `appdefs/`, `regdefs/`, `configuration/`, `sboms/`, `templates/`

**Target environment directory:**

- `environments/<cluster>/<env>`

**Shared directories** — included at site level and at cluster level:

| Site level | Cluster level |
|---|---|
| `environments/configuration` | `environments/<cluster>/configuration` |
| `environments/configurations` | `environments/<cluster>/configurations` |
| `environments/resource_profiles` | `environments/<cluster>/resource_profiles` |
| `environments/rp_override` | `environments/<cluster>/rp_override` |
| `environments/Profiles` | `environments/<cluster>/Profiles` |
| `environments/parameters` | `environments/<cluster>/parameters` |
| `environments/cloud-passport` | `environments/<cluster>/cloud-passport` |
| `environments/cloud-passports` | `environments/<cluster>/cloud-passports` |
| `environments/credentials` | `environments/<cluster>/credentials` |
| `environments/Credentials` | `environments/<cluster>/Credentials` |
| `environments/shared-credentials` | `environments/<cluster>/shared-credentials` |
| — | `environments/<cluster>/app-deployer` |
| — | `environments/<cluster>/cloud-deployer` |

When `CRED_ROTATION_PAYLOAD` is set, the entire `environments/<cluster>/` directory is added so credential rotation can scan sibling environments in the same cluster.

### Intermediate Jobs

- Do NOT checkout repository (`GIT_STRATEGY: empty`)
- Receive files and the `.git` directory from previous job's artifacts
- Modify files (optional)
- Save required paths and `.git` to job artifacts

### git_commit_job

- Receives files and the `.git` directory from previous job's artifacts
- Minimizes credential file diffs (reduces noise in commits)
- Stages only changes in the sparse-checkout paths
- Creates a detached commit (`git write-tree` + `git commit-tree`) to snapshot changes without touching any branch
- Fetches the latest state of the target branch from remote (`--depth=1`)
- Cherry-picks the snapshot commit on top of the fetched state
- Pushes to `origin HEAD:<ref>`, retrying up to 10 times with exponential backoff (start 0.3s, max 5s) on push conflicts caused by concurrent jobs

This approach avoids push failures due to stale local state: changes are always applied on top of the current remote branch tip.

## Required Artifact Paths

All jobs in the pipeline save these paths to artifacts:

- `environments/<cluster>/<env>` — target environment directory
- Shared directories under `environments/<cluster>/` and `environments/` (credentials, parameters, resource profiles, etc.)
- `appdefs/`, `regdefs/`, `configuration/`, `sboms/`, `templates/`
- `.git` — required by downstream jobs to avoid re-cloning the repository

The shared directories listed above are included in both sparse checkout and artifacts.
