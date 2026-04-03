
# Automatic Environment Name Derivation

## Problem Statement

When configuring environments in EnvGene, the `environmentName` in the Environment Inventory must traditionally be explicitly defined in the `env_definition.yml` file, even though it resides in a folder structure (`/environments/<clusterName>/<environmentName>/Inventory/`) that already implies the environment name. This redundancy increases the risk of human error if the folder name and the explicitly defined `environmentName` become inconsistent.

## Proposed Approach

### Usage

To reduce redundancy and minimize the risk of human error:

1. **Default to Folder Name**: If `environmentName` is not explicitly set in `env_definition.yml`, it will be automatically derived from the parent folder name (`<environmentName>`) in the path `/environments/<clusterName>/<environmentName>/Inventory/`.

2. **Backward Compatibility**: If `environmentName` is explicitly defined in `env_definition.yml`, it will continue to be used as the source of truth.

Example with implicit environment name (derived from folder):

```yaml
# /environments/cluster01/dev01/Inventory/env_definition.yml
inventory:
  # environmentName is not defined - will be derived from folder name "dev01"
  tenantName: "Applications"
  cloudName: "cluster01"
envTemplate:
  name: "simple"
  artifact: "project-env-template:master_20231024-080204"
```

Example with explicit environment name:

```yaml
# /environments/cluster01/dev01/Inventory/env_definition.yml
inventory:
  environmentName: "custom-name"  # Explicitly defined, overrides folder name
  tenantName: "Applications"
  cloudName: "cluster01"
envTemplate:
  name: "simple"
  artifact: "project-env-template:master_20231024-080204"
```

### Mechanics

The environment name resolution follows this logic:

1. When loading the environment definition, the system checks if `environmentName` is explicitly defined
2. If not defined, the system extracts the environment name from the directory path
3. The path structure `/environments/<clusterName>/<environmentName>/Inventory/` is parsed to identify the environment name component
4. The derived environment name is used consistently throughout the environment generation process and is available for template rendering via the `current_env.name` variable
