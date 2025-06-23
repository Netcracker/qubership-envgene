# Automatic Environment Name Derivation

- [Automatic Environment Name Derivation](#automatic-environment-name-derivation)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
  - [Implementation Details](#implementation-details)
  - [Use Cases](#use-cases)
  - [Troubleshooting](#troubleshooting)

## Problem Statement

When configuring environments in EnvGene, users face the following challenges:

1. **Redundant Configuration**: The `environmentName` in the Environment Inventory must be explicitly defined in the `env_definition.yml` file, even though it resides in a folder structure (`/environments/<clusterName>/<environmentName>/Inventory/`) that already implies the environment name.

2. **Risk of Human Error**: Manual configuration introduces the possibility of inconsistency between the folder name and the explicitly defined `environmentName`, leading to confusion and potential errors during environment deployment.

3. **Maintenance Overhead**: When renaming environments, users must update both the folder structure and the `environmentName` in the configuration file, increasing the risk of inconsistency.

Goals:

1. Reduce manual configuration effort by leveraging existing folder structure information
2. Minimize the risk of inconsistency between folder names and environment names
3. Maintain backward compatibility with existing configurations

## Proposed Approach

The solution introduces a mechanism to automatically derive the `environmentName` from the folder structure when it is not explicitly defined in the `env_definition.yml` file:

1. **Default to Folder Name**: If `environmentName` is not explicitly set in `env_definition.yml`, derive it from the parent folder name (`<environmentName>`) in the path `/environments/<clusterName>/<environmentName>/Inventory/`.

2. **Maintain Backward Compatibility**: If `environmentName` is explicitly defined in `env_definition.yml`, continue using it as the source of truth.

This approach simplifies environment configuration while preserving flexibility for cases where the environment name needs to differ from the folder name.

## Implementation Details

The environment name resolution follows this logic:

1. Check if `environmentName` is explicitly defined in the `env_definition.yml` file:
   - If defined, use the explicitly defined value
   - If not defined, extract the environment name from the folder path

2. The folder path is parsed to identify the environment name component:
   - For a path like `/environments/<clusterName>/<environmentName>/Inventory/env_definition.yml`
   - The `<environmentName>` portion is extracted as the default environment name

3. The derived environment name is used consistently throughout the environment generation process and is available for template rendering via the `current_env.name` variable.

### Implementation Areas

To implement this feature, changes would be required in the following areas of the codebase:

1. **Schema Definition**:
   - Update the JSON schema in `schemas/env-definition.schema.json` to make the `environmentName` field optional

2. **Environment Definition Processing**:
   - Modify the environment definition loading process in `scripts/build_env/build_env.py`
   - Enhance the `findEnvDefinitionFromTemplatePath` function to handle cases where `environmentName` is not defined

3. **Path Parsing Logic**:
   - Add functionality to extract the environment name from the directory path
   - Parse the path structure `/environments/<clusterName>/<environmentName>/Inventory/` to identify the environment name component

4. **Environment Context Creation**:
   - Update the environment context creation logic to use the derived name when not explicitly defined
   - Ensure the derived name is consistently used throughout the environment generation process

5. **Error Handling**:
   - Implement validation for the path structure
   - Add clear error messages for cases where the environment name cannot be determined
   - Provide troubleshooting guidance for invalid path structures

## Use Cases

### Case 1: New Environment Creation with Implicit Name

When creating a new environment without explicitly defining `environmentName`:

```yaml
# /environments/cluster-1/dev01/Inventory/env_definition.yml
inventory:
  # environmentName is not defined - will be derived from folder name "dev01"
  tenantName: "Applications"
  cloudName: "cluster-1"
envTemplate:
  name: "simple"
  artifact: "project-env-template:master_20231024-080204"
```

The system will automatically use `dev01` as the environment name.

### Case 2: Existing Environment with Explicit Name

For backward compatibility with existing environments:

```yaml
# /environments/cluster-1/dev01/Inventory/env_definition.yml
inventory:
  environmentName: "dev01"  # Explicitly defined
  tenantName: "Applications"
  cloudName: "cluster-1"
envTemplate:
  name: "simple"
  artifact: "project-env-template:master_20231024-080204"
```

The system will use the explicitly defined value `dev01` as the environment name.

### Case 3: Environment with Custom Name Different from Folder

When the environment name needs to differ from the folder name:

```yaml
# /environments/cluster-1/dev01/Inventory/env_definition.yml
inventory:
  environmentName: "development-01"  # Custom name different from folder
  tenantName: "Applications"
  cloudName: "cluster-1"
envTemplate:
  name: "simple"
  artifact: "project-env-template:master_20231024-080204"
```

The system will use `development-01` as the environment name, ignoring the folder name.

## Troubleshooting

### Common Issues

1. **Inconsistent Environment Names**:
   - **Symptom**: Environment operations fail or produce unexpected results
   - **Cause**: Mismatch between folder name and explicitly defined `environmentName`
   - **Resolution**: Ensure consistency between folder structure and configuration, or explicitly define `environmentName` if a different value is required

2. **Environment Name Not Recognized**:
   - **Symptom**: Environment name is not correctly identified during operations
   - **Cause**: Invalid folder structure or path parsing issues
   - **Resolution**: Verify that the folder structure follows the expected pattern `/environments/<clusterName>/<environmentName>/Inventory/`

3. **Template Rendering Issues**:
   - **Symptom**: Templates fail to render correctly with environment name variables
   - **Cause**: Templates expecting explicit `environmentName` in configuration
   - **Resolution**: Update templates to use `current_env.name` which will contain the correct environment name regardless of how it was derived
