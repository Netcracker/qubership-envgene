# Create an Environment Inventory

- [Create an Environment Inventory](#create-an-environment-inventory)
  - [Overview](#overview)
  - [Examples by environment type](#examples-by-environment-type)
  - [Prerequisites](#prerequisites)
  - [Choose the level of each file](#choose-the-level-of-each-file)
  - [Create an environment through the pipeline (recommended)](#create-an-environment-through-the-pipeline-recommended)
    - [Step 1: Prepare `ENV_INVENTORY_CONTENT`](#step-1-prepare-env_inventory_content)
    - [Step 2: Run the Instance pipeline](#step-2-run-the-instance-pipeline)
    - [Step 3: Verify the result](#step-3-verify-the-result)
  - [Create an environment by hand](#create-an-environment-by-hand)
    - [Step 1: Create `env_definition.yml`](#step-1-create-env_definitionyml)
    - [Step 2: Add the referenced files](#step-2-add-the-referenced-files)
    - [Step 3: Commit and generate](#step-3-commit-and-generate)
  - [Set and update credentials](#set-and-update-credentials)
  - [Related documentation](#related-documentation)

## Overview

Create the Environment Inventory of one environment: `env_definition.yml`, its ParameterSets, and its credentials
files. At the end, the Inventory is committed to the Instance repository, and with
`ENV_BUILDER: true` the Environment Instance is built from it.

Choose how to create the Inventory:

- [Through the Instance pipeline](#create-an-environment-through-the-pipeline-recommended) (recommended): pass the
  content in `ENV_INVENTORY_CONTENT`, and the pipeline writes and commits the files.
- [By hand](#create-an-environment-by-hand): commit the files yourself, when you cannot run the Instance pipeline.

For every field of `env_definition.yml` and which fields to leave out, see
[Environment Inventory](/docs/envgene-configs.md#env_definitionyml).

## Examples by environment type

Start from the example that matches your environment:

| Environment type                        | `env_definition.yml`                                                                                                                                        | Ready `ENV_INVENTORY_CONTENT`                                                                                |
|-----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| Infra: deploys the infrastructure SD    | [`env_definition.yml`](/docs/samples/infra-and-business-environments/instance-repository/environments/cluster-01/env-infra/Inventory/env_definition.yml)    | [`env-infra.json`](/docs/samples/infra-and-business-environments/env-inventory-content/env-infra.json)       |
| Business: deploys the business solution | [`env_definition.yml`](/docs/samples/infra-and-business-environments/instance-repository/environments/cluster-01/env-business/Inventory/env_definition.yml) | [`env-business.json`](/docs/samples/infra-and-business-environments/env-inventory-content/env-business.json) |

## Prerequisites

- The Instance repository is initialized. See
  [Initialize and upgrade Instance repository](/docs/how-to/envgene-maitanance.md).
- The cluster folder `/environments/<cluster-name>/` exists, with the Cloud Passport if the environment uses one.
  See [Create a cluster](/docs/how-to/create-cluster.md).
- The Environment Template is published. In `env_definition.yml`, use:
  - `envTemplate.name`: the name of the Template Descriptor in the template, the filename without extension. For
    `templates/env_templates/simple.yaml`, it is `simple`
  - `envTemplate.artifact`: the published template artifact in `application:version` form, such as
    `project-env-template:1.0.0`
- The Environment Template has an [Artifact Definition](/docs/envgene-objects.md#artifact-definition), see
  [Configure artifact registries](/docs/how-to/configure-cloud-artifact-registries.md). For
  `artifact: project-env-template:1.0.0`, it is `/configuration/artifact_definitions/project-env-template.yaml` with
  `name: project-env-template`.
- For credentials kept in the Instance repository, credential encryption is enabled. See
  [Credential encryption](/docs/how-to/credential-encryption.md).

## Choose the level of each file

ParameterSets, credentials files, and Resource Profile Overrides can live at three levels. Pick the level by who uses
the file:

| Level       | Use it for                                          | `place` in `ENV_INVENTORY_CONTENT` |
|-------------|-----------------------------------------------------|------------------------------------|
| Environment | values of this environment only                     | `env`                              |
| Cluster     | values shared by all environments of one cluster    | `cluster`                          |
| Repository  | values shared by all environments in the repository | `site`                             |

Each level has its own folder:

| File                      | Environment                                                 | Cluster                                     | Repository                        |
|---------------------------|-------------------------------------------------------------|---------------------------------------------|-----------------------------------|
| ParameterSet              | `environments/<cluster>/<env>/Inventory/parameters/`        | `environments/<cluster>/parameters/`        | `environments/parameters/`        |
| Credentials file          | `environments/<cluster>/<env>/Inventory/credentials/`       | `environments/<cluster>/credentials/`       | `environments/credentials/`       |
| Resource Profile Override | `environments/<cluster>/<env>/Inventory/resource_profiles/` | `environments/<cluster>/resource_profiles/` | `environments/resource_profiles/` |

`env_definition.yml` refers to a file by name, not by level. EnvGene looks for the name at the environment level
first, then at the cluster level, then at the repository level, and uses the first match. A file at the environment
level therefore hides a file with the same name at the cluster or repository level. For the full search order, see
[File resolution for shared entities](/docs/envgene-configs.md#file-resolution-for-shared-entities).

> [!WARNING]
> A file at the cluster or repository level is shared. If a pipeline run for one environment replaces or deletes it,
> the change applies to every environment that uses the file.

## Create an environment through the pipeline (recommended)

### Step 1: Prepare `ENV_INVENTORY_CONTENT`

Write the content as JSON. This example creates `env_definition.yml` and one ParameterSet for `cluster-01/env-01`:

```json
{
  "envDefinition": {
    "action": "create_or_replace",
    "content": {
      "inventory": {
        "noCmdbVersion": "v2"
      },
      "envTemplate": {
        "name": "simple",
        "artifact": "project-env-template:1.0.0",
        "envSpecificE2EParamsets": {
          "cloud": [
            "cloud-pipeline"
          ]
        }
      }
    }
  },
  "paramSets": [
    {
      "action": "create_or_replace",
      "place": "env",
      "content": {
        "name": "cloud-pipeline",
        "version": 1,
        "parameters": {
          "DEPLOYMENT_TIMEOUT": "1800"
        }
      }
    }
  ]
}
```

- `envSpecificE2EParamsets` binds ParameterSets by name. The key `cloud` applies them to the whole environment. A
  Namespace folder name from `Namespaces/` applies them to that Namespace only.
- Every name in `envSpecificE2EParamsets` must match a ParameterSet that the same content creates or that already
  exists in the repository.
- To add credentials in the same run, see [Configure Local Credentials](/docs/how-to/configure-local-credentials.md)
  or [Configure External Credentials](/docs/how-to/configure-external-credentials.md).
- `place` sets the level of each file, see [Choose the level of each file](#choose-the-level-of-each-file).

For all blocks, see [Environment Inventory Generation](/docs/features/env-inventory-generation.md).
For all fields of `envDefinition.content`, see [`env_definition.yml`](/docs/envgene-configs.md#env_definitionyml).

### Step 2: Run the Instance pipeline

Pass the JSON from Step 1 as a single-line string:

```yaml
ENV_NAMES: cluster-01/env-01
ENV_INVENTORY_CONTENT: <JSON from Step 1>
ENV_BUILDER: true
```

`ENV_BUILDER: true` renders the Environment Instance in the same run. Leave it out to create only the Inventory.

### Step 3: Verify the result

After the pipeline commits, the Inventory of the environment contains:

```text
environments/
└── cluster-01/
    └── env-01/
        └── Inventory/
            ├── env_definition.yml
            └── parameters/
                └── cloud-pipeline.yml
```

With `ENV_BUILDER: true`, the folder `environments/cluster-01/env-01/` also holds the generated Environment Instance:
`cloud.yml`, `tenant.yml`, `Namespaces/`, and `Credentials/`.

If the job fails with a schema error, check the JSON against
[`env-inventory-content.schema.json`](/schemas/env-inventory-content.schema.json).

## Create an environment by hand

### Step 1: Create `env_definition.yml`

Create the file:

```yaml
# environments/cluster-01/env-01/Inventory/env_definition.yml
inventory:
  noCmdbVersion: "v2"
envTemplate:
  name: simple
  artifact: project-env-template:1.0.0
  envSpecificE2EParamsets:
    cloud:
      - cloud-pipeline
```

### Step 2: Add the referenced files

Create every ParameterSet and credentials file that `env_definition.yml` references. For the example above:

```yaml
# environments/cluster-01/env-01/Inventory/parameters/cloud-pipeline.yml
name: cloud-pipeline
version: 1
parameters:
  DEPLOYMENT_TIMEOUT: "1800"
```

To share a file between environments, put it in the cluster or repository folder, see
[Choose the level of each file](#choose-the-level-of-each-file).

### Step 3: Commit and generate

1. Commit the files to the Instance repository.
2. Run the Instance pipeline with `ENV_NAMES: cluster-01/env-01` and `ENV_BUILDER: true`.

## Set and update credentials

To set the credential values of the environment and change them later, see
[Configure Local Credentials](/docs/how-to/configure-local-credentials.md), or
[Configure External Credentials](/docs/how-to/configure-external-credentials.md) for a Secret Store.

## Related documentation

- [Environment Inventory](/docs/envgene-configs.md#env_definitionyml)
- [Environment Inventory Generation](/docs/features/env-inventory-generation.md)
- [Split a Cloud Passport for business and infra environments](/docs/how-to/split-cloud-passport-for-business-and-infra.md)
- [Create a cluster](/docs/how-to/create-cluster.md)
- [Configure Local Credentials](/docs/how-to/configure-local-credentials.md)
- [Configure External Credentials](/docs/how-to/configure-external-credentials.md)
- [Credential Rotation](/docs/features/cred-rotation.md)
