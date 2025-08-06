# On-Commit Build Workflow Documentation

This document describes how to use the automated Docker image build workflow for Qubership EnvGene project.

- [On-Commit Build Workflow Documentation](#on-commit-build-workflow-documentation)
  - [CI/CD Pipeline Architecture](#cicd-pipeline-architecture)
    - [Parallel Execution on Commits](#parallel-execution-on-commits)
    - [Pull Request Workflow](#pull-request-workflow)
  - [Docker Images Built](#docker-images-built)
  - [Automatic Triggering](#automatic-triggering)
    - [Commit Message Format](#commit-message-format)
    - [Supported Commit Types](#supported-commit-types)
    - [Examples of Valid Commit Messages](#examples-of-valid-commit-messages)
    - [Commit Message Behavior](#commit-message-behavior)
  - [Manual Execution](#manual-execution)
    - [How to Run Manually](#how-to-run-manually)
    - [Manual Build Options](#manual-build-options)
    - [Manual Execution Scenarios](#manual-execution-scenarios)
      - [Build All Images (Default)](#build-all-images-default)
      - [Build Single Image](#build-single-image)
      - [Build Multiple Images](#build-multiple-images)
  - [Docker images execution Flow](#docker-images-execution-flow)
    - [Special Case: Effective Set Generator](#special-case-effective-set-generator)
  - [Image Registry](#image-registry)
    - [Example Image Names](#example-image-names)
  - [Troubleshooting](#troubleshooting)
    - [Workflow Not Triggering](#workflow-not-triggering)
    - [Job Skipped](#job-skipped)
    - [Build Failures](#build-failures)
  - [Best Practices](#best-practices)
    - [Commit Messages Best Practices](#commit-messages-best-practices)
    - [Manual Execution Best Practices](#manual-execution-best-practices)
    - [Monitoring Best Practices](#monitoring-best-practices)
  - [Code Quality Workflows](#code-quality-workflows)
    - [Super Linter](#super-linter)
      - [Triggering Conditions](#triggering-conditions)
      - [What It Does](#what-it-does)
      - [Configuration](#configuration)
    - [Link Checker](#link-checker)
      - [Link Checker Triggering Conditions](#link-checker-triggering-conditions)
      - [What Link Checker Does](#what-link-checker-does)
      - [Link Checker Configuration](#link-checker-configuration)
  - [Related Files](#related-files)

## CI/CD Pipeline Architecture

When commits are pushed to any branch (except `main`), the following workflows run in parallel:

### Parallel Execution on Commits

1. **Super Linter** (`.github/workflows/super-linter.yaml`)
   - Checks code quality and style
   - Validates syntax and formatting
   - Runs across all supported languages

2. **Link Checker** (`.github/workflows/link-checker.yaml`)
   - Validates all links in markdown files
   - Ensures documentation links are working

3. **Conditional Execution Based on Commit Message**:

   **For commits with `fix:`, `feat:`, or `BREAKING CHANGE:`**:
   - **Docker Builds** (`.github/workflows/build-all-docker-images.yml`)
     - Builds and pushes Docker images to registry
     - Runs after code quality checks pass

   **For commits WITHOUT conventional commit prefixes**:
   - **Tests** (`.github/workflows/perform_tests.yml`)
     - Runs unit and integration tests
     - Validates code functionality

### Pull Request Workflow

On pull requests, the following workflows run regardless of commit message format:

- Super Linter
- Link Checker  
- Tests

This ensures comprehensive validation before code is merged. Docker builds are not triggered on pull requests to avoid unnecessary builds during code review.

## Docker Images Built

The workflow builds four Docker images:

1. **Qubership GCIP** (`qubership-gcip`)
2. **Qubership Envgene** (`qubership-envgene`)
3. **Instance Repo Pipeline** (`qubership-instance-repo-pipeline`)
4. **Effective Set Generator** (`qubership-effective-set-generator`)

## Automatic Triggering

### Commit Message Format

The Docker build workflow automatically triggers when commits are pushed with conventional commit prefixes. Use conventional commit format:

```yaml
<type>: <description>
```

### Supported Commit Types

| Type | Description | Example |
|------|-------------|---------|
| `feat:` | New features | `feat: add new authentication system` |
| `fix:` | Bug fixes | `fix: resolve docker build issue` |
| `BREAKING CHANGE:` | Breaking changes | `BREAKING CHANGE: major refactor` |

### Examples of Valid Commit Messages

```bash
git commit -m "feat: add new docker build optimization"
git commit -m "fix: resolve effective-set generator build issue"
git commit -m "BREAKING CHANGE: major refactor of build system"
```

### Commit Message Behavior

- **Commits with `feat:`, `fix:`, or `BREAKING CHANGE:`** → Triggers Docker builds
- **Commits without conventional prefixes** → Triggers tests only
- **All commits** → Trigger code quality checks (Linter + Link Checker)

## Manual Execution

### How to Run Manually

1. Go to the **Actions** tab in your GitHub repository
2. Select **"Dev: Build Qubership EnvGene docker images"** workflow
3. Click **"Run workflow"** button
4. Configure the build options (see below)
5. Click **"Run workflow"** to start

### Manual Build Options

When running manually, you can choose which images to build:

| Option | Description | Default |
|--------|-------------|---------|
| `build-gcip` | Build Qubership GCIP image | ✅ Enabled |
| `build-envgene` | Build Qubership Envgene image | ✅ Enabled |
| `build-pipeline` | Build Instance Repo Pipeline image | ✅ Enabled |
| `build-effective-set` | Build Effective Set Generator image | ✅ Enabled |

### Manual Execution Scenarios

#### Build All Images (Default)

- Leave all options enabled
- All four Docker images will be built

#### Build Single Image

- Disable three options, enable only the one you need
- Example: Enable only `build-envgene` to build just the Envgene image

#### Build Multiple Images

- Enable only the specific images you need
- Example: Enable `build-gcip` and `build-envgene` to build two images

## Docker images execution Flow

1. **Tests** - Runs first and must pass
2. **Build Jobs** - Run in parallel after tests pass:
   - `build-qubership-gcip`
   - `build-qubership-envgene`
   - `build-instance-repo-pipeline`
   - `build-effective-set-jar --> build-effective-set-generator`

### Special Case: Effective Set Generator

The Effective Set Generator has a two-step build process:

1. **build-effective-set-jar** - Builds Java JAR using Maven
2. **build-effective-set-generator** - Builds Docker image using the JAR

## Image Registry

All images are pushed to **GitHub Container Registry (ghcr.io)** with the following naming convention:

```text
ghcr.io/<repository-owner>/<image-name>
```

### Example Image Names

- `ghcr.io/netcracker/qubership-gcip`
- `ghcr.io/netcracker/qubership-envgene`
- `ghcr.io/netcracker/qubership-instance-repo-pipeline`
- `ghcr.io/netcracker/qubership-effective-set-generator`

## Troubleshooting

### Workflow Not Triggering

**Problem**: Workflow doesn't run on commit push

**Solutions**:

1. Check commit message format - must start with `feat:`, `fix:`, or `BREAKING CHANGE:`
2. Verify files changed are not in ignored paths
3. Ensure you're pushing to a branch (not a tag)

### Job Skipped

**Problem**: Some jobs are skipped during execution

**Solutions**:

1. For manual runs: Check if the corresponding option is enabled
2. For automatic runs: Verify commit message format
3. Check job dependencies - some jobs require others to complete first

### Build Failures

**Problem**: Docker build fails

**Solutions**:

1. Check Dockerfile syntax and paths
2. Verify required secrets are configured:
   - `GITHUB_TOKEN` (automatic)
   - `GIT_USER` (for GCIP and Effective Set)
   - `GIT_TOKEN` (for GCIP and Effective Set)
   - `GH_ACCESS_TOKEN` (for Envgene and Pipeline)
3. Check if Dockerfile exists in the specified path

## Best Practices

### Commit Messages Best Practices

- Use [conventional commit format](https://www.conventionalcommits.org/en/v1.0.0/) consistently
- Be descriptive in commit messages
- Use appropriate commit types: `feat:`, `fix:`, or `BREAKING CHANGE:`

### Manual Execution Best Practices

- Use manual execution for testing specific images
- Disable unnecessary builds to save time and resources
- Test individual images before building all

### Monitoring Best Practices

- Monitor workflow runs in the Actions tab
- Check build logs for any issues
- Verify images are pushed to the registry

## Code Quality Workflows

### Super Linter

The `super-linter.yaml` workflow automatically checks code quality and style across the entire codebase.

#### Triggering Conditions

- **Push events**: Runs on commits to any branch except `main`
- **Pull requests**: Runs on all pull requests to any branch
- **Manual execution**: Can be triggered manually via workflow dispatch

#### What It Does

- Lints code based on file extensions and languages detected
- Checks for code style violations
- Validates syntax and formatting
- Supports multiple programming languages (Python, YAML, JSON, etc.)

#### Configuration

- Configuration files should be placed in `.github/linters/`
- Environment variables can be set in `.github/super-linter.env`
- Supports full codebase scan via manual execution with `full_scan: true`

### Link Checker

The `link-checker.yaml` workflow validates all links in markdown files to ensure they are working correctly.

#### Link Checker Triggering Conditions

- **Push events**: Runs on commits to any branch except `main`
- **Pull requests**: Runs on all pull requests to any branch
- **Manual execution**: Can be triggered manually via workflow dispatch

#### What Link Checker Does

- Scans all `.md` files in the repository
- Validates HTTP/HTTPS links
- Reports broken or inaccessible links
- Accepts status codes: 100-103, 200-299, 429 (rate limiting)

#### Link Checker Configuration

- Uses Lychee link checker tool
- Accepts certain HTTP status codes as valid (rate limiting, redirects)
- Fails the workflow if broken links are found

## Related Files

- **Workflow**: `.github/workflows/build-all-docker-images.yml`
- **Composite Actions**: `.github/actions/build-*`
- **Dockerfiles**: Located in respective build directories
- **Test Workflow**: `.github/workflows/perform_tests.yml`
- **Linter Workflow**: `.github/workflows/super-linter.yaml`
- **Link Checker Workflow**: `.github/workflows/link-checker.yaml`
