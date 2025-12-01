# Build and Usage Guide for envgene-instance-project Package

## Description

The `envgene-instance-project` package is a Gear for git-system-follower (gsf) that automates the creation and management of GitLab CI/CD file structure for envgene instance projects. The package uses cookiecutter to generate file templates.

## Package Structure

```
envgene_instance_project/
├── Dockerfile                                    # Dockerfile for building the image
└── git-system-follower-package/
    ├── package.yaml                              # Package metadata
    └── scripts/
        └── 1.0.0/                               # Package version
            ├── init.py                          # Installation script
            ├── update.py                        # Update script
            ├── delete.py                        # Removal script
            └── templates/
                └── default/
                    ├── cookiecutter.json        # Cookiecutter variables
                    └── {{ cookiecutter.gsf_repository_name }}/
                        └── {{ cookiecutter.project_name }}/
                            └── gitlab-ci/
                                └── pipeline_vars.yaml
```

## Building Docker Image

### Prerequisites

- Docker installed and running
- Access to Docker registry (optional, for publishing the image)

### Building the Image

1. Navigate to the package directory:
```bash
cd gsf_packages/envgene_instance_project
```

2. Build the Docker image:
```bash
docker build -t envgene-instance-project:1.0.0 .
```

Where:
- `envgene-instance-project` — image name
- `1.0.0` — version (must match the version in `package.yaml`)

### Publishing the Image to Registry

If you want to publish the image to a Docker registry:

```bash
# Log in to registry (if required)
docker login <your-registry-url>

# Tag the image for registry
docker tag envgene-instance-project:1.0.0 <registry>/envgene-instance-project:1.0.0

# Publish the image
docker push <registry>/envgene-instance-project:1.0.0
```

Example:
```bash
docker tag envgene-instance-project:1.0.0 ghcr.io/netcracker/envgene-instance-project:1.0.0
docker push ghcr.io/netcracker/envgene-instance-project:1.0.0
```

## Installing git-system-follower (gsf)

If gsf is not yet installed:

### Installation via pip

```bash
pip install qubership-git-system-follower
```

### Verify Installation

```bash
gsf version
```

## Using the Package

### Prerequisites

1. **GitLab Repository**: Create or select a GitLab repository where the package will be installed
2. **GitLab Access Token**: Create an access token with the following permissions:
   - `api`: Full API access
   - `read_api`: Read API access
   - `read_repository`: Repository read access
   - `write_repository`: Repository write access

3. **Export the token**:
```bash
export GSF_GIT_TOKEN=<your-gitlab-token>
```

### Installing the Package

#### Installation from Local Image

If you built the image locally and want to install it directly:

```bash
gsf install \
  --repo https://gitlab.com/<group>/<repository> \
  --branch main \
  envgene-instance-project:1.0.0 \
  --extra project_name my-project no-masked \
  --extra docker_registry ghcr.io/netcracker no-masked \
  --extra ENV_NAMES "test-cluster/e01" no-masked \
  --extra ENV_BUILDER "true" no-masked \
  --extra ENV_TEMPLATE_VERSION "qubership_envgene_templates:0.0.1" no-masked \
  --extra DEPLOYMENT_TICKET_ID "TEST-1111" no-masked \
  --extra DEPLOYMENT_SESSION_ID "" no-masked \
  --extra GITLAB_RUNNER_TAG_NAME "local" no-masked
```

#### Installation from Docker Registry

If the image is published in a registry:

```bash
gsf install \
  --repo https://gitlab.com/<group>/<repository> \
  --branch main \
  <registry>/envgene-instance-project:1.0.0 \
  --extra project_name my-project no-masked \
  --extra docker_registry ghcr.io/netcracker no-masked \
  --extra ENV_NAMES "test-cluster/e01" no-masked \
  --extra ENV_BUILDER "true" no-masked \
  --extra ENV_TEMPLATE_VERSION "qubership_envgene_templates:0.0.1" no-masked \
  --extra DEPLOYMENT_TICKET_ID "TEST-1111" no-masked \
  --extra DEPLOYMENT_SESSION_ID "" no-masked \
  --extra GITLAB_RUNNER_TAG_NAME "local" no-masked
```

#### Installation Parameters

- `--repo`: GitLab repository URL
- `--branch`: Branch where the package will be installed (can specify multiple with `-b`)
- `--extra`: Additional variables for the cookiecutter template
  - Format: `--extra <variable_name> <value> <masked|no-masked>`
  - `masked`: Value will be hidden in logs
  - `no-masked`: Value will be visible in logs

#### Available Cookiecutter Variables

All variables from `cookiecutter.json` can be passed via `--extra`:

- `project_name`: Project name (default: `my-project`)
- `docker_registry`: Docker registry (default: `ghcr.io/netcracker`)
- `ENV_NAMES`: Environment names (default: `test-cluster/e01`)
- `ENV_BUILDER`: Builder flag (default: `true`)
- `ENV_TEMPLATE_VERSION`: Template version (default: `qubership_envgene_templates:0.0.1`)
- `DEPLOYMENT_TICKET_ID`: Deployment ticket ID (default: `TEST-1111`)
- `DEPLOYMENT_SESSION_ID`: Deployment session ID (default: empty string)
- `GITLAB_RUNNER_TAG_NAME`: GitLab runner tag (default: `local`)

### What Gets Created During Installation

After installation, the following structure will be created in the repository:

```
<repository-root>/
├── .state.yaml                                  # gsf state file (created automatically)
└── <project_name>/                              # Name from project_name variable
    └── gitlab-ci/
        └── pipeline_vars.yaml                   # CI/CD variables file
```

The `pipeline_vars.yaml` file will contain variables passed via `--extra` or default values from `cookiecutter.json`.

### Updating the Package

To update the package to a new version:

```bash
gsf install \
  --repo https://gitlab.com/<group>/<repository> \
  --branch main \
  <registry>/envgene-instance-project:1.1.0 \
  --extra project_name my-project no-masked \
  --extra docker_registry ghcr.io/netcracker no-masked
```

gsf will automatically perform migration between versions if necessary.

### Removing the Package

To remove the package from the repository:

```bash
gsf uninstall \
  --repo https://gitlab.com/<group>/<repository> \
  --branch main \
  <registry>/envgene-instance-project:1.0.0
```

During removal, only files created by the package will be removed, without modifying user files.

## How Cookiecutter Works Inside gsf

### Workflow

1. **During Installation (init.py)**:
   - gsf calls `create_template()` with template name `default`
   - Variables from `--extra` are passed to cookiecutter
   - cookiecutter generates files from the template in `templates/default/`
   - Files are copied to the target repository, considering existing files

2. **During Update (update.py)**:
   - gsf calls `update_template()` 
   - Files from current and new versions are compared
   - Only files that haven't been modified by the user are updated

3. **During Removal (delete.py)**:
   - gsf calls `delete_template()`
   - Only files matching the template are removed
   - User modifications are preserved

### Cookiecutter Template Structure

The template should be located at:
```
scripts/<version>/templates/<template_name>/
├── cookiecutter.json
└── {{ cookiecutter.gsf_repository_name }}/
    └── <file structure>
```

**Important**: 
- The template root directory must be named `{{ cookiecutter.gsf_repository_name }}`
- The `cookiecutter.json` must contain a variable `gsf_repository_name` with an empty value: `"gsf_repository_name": ""`
- gsf automatically substitutes the repository name into this variable

### Using Variables in Templates

You can use variables from `cookiecutter.json` in template files:

```yaml
# Example usage in pipeline_vars.yaml
variables:
  ENV_NAMES: "{{ cookiecutter.ENV_NAMES | default('test-cluster/e01') }}"
  PROJECT_NAME: "{{ cookiecutter.project_name }}"
```

The `default()` filter allows you to specify a default value if the variable is not passed.

## Debugging

### Enabling Debug Mode

To get detailed information about gsf operation:

```bash
gsf install --debug \
  --repo https://gitlab.com/<group>/<repository> \
  --branch main \
  <registry>/envgene-instance-project:1.0.0 \
  --extra project_name my-project no-masked
```

### Viewing State File

After installation, a `.state.yaml` file is created in the repository, which contains information about installed packages:

```yaml
hash: <hash>
packages:
  - name: envgene-instance-project
    version: 1.0.0
    used_template: default
    template_variables:
      project_name: <masked_value>
      ENV_NAMES: <masked_value>
    # ...
```

This file is used by gsf to track state and should not be edited manually.

## Usage Examples

### Minimal Installation

```bash
gsf install \
  --repo https://gitlab.com/mygroup/myproject \
  --branch main \
  envgene-instance-project:1.0.0 \
  --extra project_name my-project no-masked
```

Default values from `cookiecutter.json` are used.

### Full Installation with Custom Values

```bash
gsf install \
  --repo https://gitlab.com/mygroup/myproject \
  --branch main \
  ghcr.io/netcracker/envgene-instance-project:1.0.0 \
  --extra project_name production-project no-masked \
  --extra docker_registry registry.company.com no-masked \
  --extra ENV_NAMES "prod-cluster/p01,prod-cluster/p02" no-masked \
  --extra ENV_BUILDER "false" no-masked \
  --extra ENV_TEMPLATE_VERSION "qubership_envgene_templates:1.0.0" no-masked \
  --extra DEPLOYMENT_TICKET_ID "PROD-1234" no-masked \
  --extra GITLAB_RUNNER_TAG_NAME "production" no-masked
```

### Installation to Multiple Branches

```bash
gsf install \
  --repo https://gitlab.com/mygroup/myproject \
  --branch main \
  --branch develop \
  --branch staging \
  envgene-instance-project:1.0.0 \
  --extra project_name my-project no-masked
```

## Troubleshooting

### Error "Template is missing"

Make sure the package structure is correct and the template is located in `scripts/<version>/templates/default/`.

### Error "Gears for installation are not specified"

Check the image specification format. Either a local image or a full path to the image in the registry must be specified.

### GitLab Authentication Error

Check:
- Correctness of the GitLab token in the `GSF_GIT_TOKEN` variable
- Token access permissions (should be `api`, `read_api`, `read_repository`, `write_repository`)
- GitLab repository accessibility

### Files Are Not Created

Check:
- Write permissions to the repository
- Logs with the `--debug` flag for detailed information
- Existence of the branch specified in `--branch`

## Additional Resources

- [git-system-follower Documentation](https://netcracker.github.io/qubership-git-system-follower/latest/home/)
- [Cookiecutter Documentation](https://cookiecutter.readthedocs.io/)
- [Gear Creation Guide](https://netcracker.github.io/qubership-git-system-follower/latest/concepts/gears/)
