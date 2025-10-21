# Environment Creation Guide

- [Environment Creation Guide](#environment-creation-guide)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Manual Environment Creation](#manual-environment-creation)
    - [Manual Flow](#manual-flow)
  - [Environment Creation Using Pipeline](#environment-creation-using-pipeline)
    - [Pipeline Flow](#pipeline-flow)
  - [Results](#results)

## Description

This guide describes the process of creating a new environment in the Instance repository, either manually or using an automated pipeline.

## Prerequisites

- The Instance repository has already been initialized and follows the standard structure.

- The cluster has already been created. (Refer to the [cluster creation guide](/docs/how-to/create-cluster.md) for details.)

## Manual Environment Creation

### Manual Flow

1. **Clone (pull updates from) the remote Instance repository to the local machine.**

2. **Create the required environment folder inside `/environments/<cluster-name>`.**
   - `<cluster-name>` is the name of the target cluster (e.g., `example-cloud`)
   - `<env-name>` is the name of the environment (e.g., `env-1`)

    ```plaintext
    ├── environments
    │   ├── <cluster-name>
    │   │   ├── <env-name>
    ```

3. **Inside the environment folder, create an `Inventory` directory:**

    ```plaintext
    ├── environments
    │   ├── <cluster-name>
    │   │   ├── <env-name>
    │   │   │   ├── Inventory
    ```

    **Note:** Folder name must be `Inventory` (case-sensitive).

4. **Inside the Inventory folder, create the file `env_definition.yml`:**

    Refer to [env_definition.yml](/docs/envgene-configs.md#env_definitionyml)

    ```plaintext
    ├── environments
    │   ├── <cluster-name>
    │   │   ├── <env-name>
    │   │   │   ├── Inventory
    │   │   │   │   ├── env_definition.yml
    ```

    **Note:** File name must be `env_definition.yml`.

5. **Commit and push the changes to the remote repository**

## Environment Creation Using Pipeline

### Pipeline Flow

1. **Trigger the environment generation pipeline in the Instance repository.**

2. **Specify the following input parameters when triggering the pipeline:**
   - `ENV_NAMES`: Full environment path in the format `<cluster-name>/<env-name>`
   - `ENV_INVENTORY_INIT`: Set to true to generate a new environment inventory
   - Optionally, provide `ENV_SPECIFIC_PARAMS` to define environment-specific configuration, parameters, or credentials
  
3. **The pipeline will automatically:**
   - Create the required folder structure under `/environments/<cluster-name>/<env-name>`
   - Generate the `Inventory` directory and `env_definition.yml` file
   - Optionally create:
       - Parameter Sets under `/Inventory/parameters/`
       - Credential files under `/Credentials/`
   - Commit and push the generated structure to the remote Instance repository

    > **Note:** You do not need to commit or push any files manually; the pipeline performs all repository operations automatically.

## Results

- The new environment inventory is now available in the remote Instance repository.
- You can now proceed with environment-specific operations such as configuration or deployment.

**Note:** Pass the full path `<cluster-name>/<env-name>` to the `ENV_NAMES` input parameter when executing environment operations.
