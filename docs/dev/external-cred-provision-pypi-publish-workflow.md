# External Credentials CLI PyPI publish workflow

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Workflow file](#workflow-file)
- [Pipeline overview](#pipeline-overview)
- [Publish mode vs build-only mode](#publish-mode-vs-build-only-mode)
- [How to run a release](#how-to-run-a-release)
- [Version rules](#version-rules)
- [Job summaries](#job-summaries)
- [Helper scripts](#helper-scripts)
- [Troubleshooting](#troubleshooting)
- [Related files](#related-files)

## Description

The workflow
[Publish to PyPI: qubership-external-cred-provision](/.github/workflows/external-cred-provision-pypi-publish.yaml)
builds, tests, and optionally publishes the `qubership-external-cred-provision` Python package to the public PyPI
index. After a successful publish on upstream `main`, it commits the release version back to
`python/external-cred-provision/pyproject.toml`.

Use this workflow when you need a verified wheel and sdist for the External Credentials provisioning CLI, or when
you are cutting a new PyPI release.

## Prerequisites

### Repository secrets

Configure these secrets on `Netcracker/qubership-envgene`:

| Secret            | Purpose                                      |
|-------------------|----------------------------------------------|
| `PYPI_API_TOKEN`  | PyPI API token (must start with `pypi-`)     |

The workflow passes the token to Poetry as `POETRY_PYPI_TOKEN_PYPI`. No PyPI username secret is required.

### GitHub App for version-bump push (required on protected `main`)

| Setting                           | Purpose                                   |
|-----------------------------------|-------------------------------------------|
| Variable `GH_BUMP_VERSION_APP_ID` | GitHub App ID for version-bump pushes     |
| Secret `GH_BUMP_VERSION_APP_KEY`  | GitHub App private key                    |

Configure both on `Netcracker/qubership-envgene`. The `sync-repo-version` job uses an app installation token to
push the `pyproject.toml` version bump when `main` is protected (same app as
[Release: EnvGene](/.github/workflows/docker_publish_release.yml)).

If either value is missing, the app token step is skipped and the job falls back to `GITHUB_TOKEN`. That fallback
works only when branch protection allows `github-actions[bot]` to push.

## Workflow file

Path: [/.github/workflows/external-cred-provision-pypi-publish.yaml](/.github/workflows/external-cred-provision-pypi-publish.yaml)

Key environment variables:

| Variable                    | Value                                      |
|-----------------------------|--------------------------------------------|
| `PROJECT_DIR`               | `python/external-cred-provision`           |
| `PACKAGE_NAME`              | `qubership-external-cred-provision`        |
| `CLI_NAME`                  | `external-cred-provision`                  |
| `UPSTREAM_REPO`             | `Netcracker/qubership-envgene`             |
| `PYPI_SCRIPTS_DIR`          | `.github/scripts/pypi`                     |
| `POETRY_VERSION`            | `2.1.3`                                    |
| `PYPI_RETRY_ATTEMPTS`       | `3`                                        |
| `PYPI_RETRY_DELAY_SECONDS`  | `30`                                       |

`PACKAGE_NAME` is the PyPI distribution name. `CLI_NAME` is the console command installed on `PATH` (shorter).

GitHub Actions artifact name: `${PACKAGE_NAME}-dist-${version}` (for example
`qubership-external-cred-provision-dist-0.0.1`).

## Pipeline overview

```text
gate → validate-input → build-package → publish-package → sync-repo-version
```

| Job                 | Runs when                         | Purpose |
|---------------------|-----------------------------------|---------|
| `gate`              | Always                            | Sets `can_publish` for upstream `main` only |
| `validate-input`    | Always                            | Validates SemVer; checks PyPI bump in publish mode |
| `build-package`     | After validation                  | Tests, builds, smoke-tests CLI, uploads artifact |
| `publish-package`   | `can_publish == true`             | Publishes to PyPI with Poetry and verifies the release |
| `sync-repo-version` | Publish succeeded on upstream     | Commits `pyproject.toml` version bump |

Concurrency group `pypi-external-cred-provision` prevents overlapping runs. In-progress runs are not cancelled.

## Publish mode vs build-only mode

**Publish mode** applies when all of these are true:

- The repository is not a fork.
- The repository is `Netcracker/qubership-envgene`.
- The ref is `refs/heads/main`.

In publish mode the workflow uploads to PyPI, verifies the release, and syncs the repository version.

**Build-only mode** applies on forks, feature branches, or non-upstream repositories. The workflow still validates
SemVer, runs tests, builds distributions, smoke-tests the CLI, and uploads a GitHub Actions artifact. PyPI upload
and repository sync are skipped.

## How to run a release

1. Open **Actions** in GitHub and select **Publish to PyPI: qubership-external-cred-provision**.
2. Click **Run workflow**.
3. Enter the release version in strict SemVer form (`X.Y.Z`, for example `0.0.1`).
4. Run the workflow from upstream `main` to publish. Run from a fork or branch to validate the build only.
5. After success, check the job summaries on `build-package`, `publish-package`, and `sync-repo-version`.

Published package URL pattern:

`https://pypi.org/project/qubership-external-cred-provision/<version>/`

Install after release:

```bash
pip install qubership-external-cred-provision==<version>
```

Run the CLI as `external-cred-provision` after install.

## Version rules

- Input must match strict SemVer: `X.Y.Z` with no `v` prefix and no prerelease suffix.
- In publish mode, the candidate version must be **greater than** the latest version already on PyPI.
- The first release is allowed when the package does not exist on PyPI yet (PyPI returns `404`).
- The build job sets `[project].version` in the working tree for the artifact only. The committed version on
  `main` updates in `sync-repo-version` after a successful publish.

## Job summaries

Each major job writes a Markdown table to `$GITHUB_STEP_SUMMARY`:

| Job               | Summary contents |
|-------------------|------------------|
| `build-package`   | Package name, version, artifact name, build-only vs publish mode |
| `publish-package` | Package name, version, CLI name, PyPI link |
| `sync-repo-version` | Package name, version, sync commit link (or skip note), PyPI link |

Open the job in the Actions run and expand **Summary** to read them.

## Helper scripts

| Script | Role |
|--------|------|
| [/.github/scripts/pypi/check_pypi_version.py](/.github/scripts/pypi/check_pypi_version.py) | SemVer validation, bump check, post-publish verification |
| [/.github/scripts/pypi/check_pypi_credentials.py](/.github/scripts/pypi/check_pypi_credentials.py) | PyPI reachability and token shape preflight |
| [/.github/scripts/pypi/set_pyproject_version.py](/.github/scripts/pypi/set_pyproject_version.py) | Updates `[project].version` in `pyproject.toml` |
| [/.github/scripts/pypi/retry_command.sh](/.github/scripts/pypi/retry_command.sh) | Shared retry helper for transient PyPI failures |

Exit codes from `check_pypi_version.py`:

| Code | Meaning |
|------|---------|
| `0`  | Success |
| `1`  | Validation error (bad SemVer or version not bumped) |
| `2`  | PyPI query error (retried) |
| `3`  | Published version not indexed yet (retried after upload) |

## Troubleshooting

### Version bump check fails

The candidate version is not greater than the latest PyPI release. Pick a higher `X.Y.Z` value.

### Token preflight fails

Check `PYPI_API_TOKEN`. The value must start with `pypi-` and must not include leading or trailing whitespace.

Create a new API token on [pypi.org](https://pypi.org) with **Entire account** scope for a first release, or project scope for
`qubership-external-cred-provision`.

### Poetry publish fails with HTTP 403

The token lacks upload permission for this package, or the secret value is wrong. Replace `PYPI_API_TOKEN` and re-run the
workflow. Preflight checks reachability and token shape only. Upload authorization is enforced by `poetry publish`.

### Publish succeeds but sync commit fails

If `GH_BUMP_VERSION_APP_ID` or `GH_BUMP_VERSION_APP_KEY` is missing on protected `main`, the sync push fails or
is rejected. Configure both app settings (same as the EnvGene release workflow) or adjust branch protection rules,
or commit the version bump manually.

### Build-only on a fork when you expected publish

Publish runs only on upstream `main`. Merge to `Netcracker/qubership-envgene` `main` and re-run from there.

### CLI layout check fails

`pyproject.toml` `[project.scripts]` must define an entry point named `external-cred-provision` matching
`CLI_NAME` in the workflow.

## Related files

- Package source: [/python/external-cred-provision/](/python/external-cred-provision/)
- Package readme (PyPI long description): [/python/external-cred-provision/README.md](/python/external-cred-provision/README.md)
- CLI feature reference: [/docs/features/external-creds-provisioning-cli.md](/docs/features/external-creds-provisioning-cli.md)
- Artifact naming conventions: [/docs/dev/artifact-naming.md](/docs/dev/artifact-naming.md)
