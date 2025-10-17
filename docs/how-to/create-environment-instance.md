# Environment Creation Guide

- [Environment Creation Guide](#environment-creation-guide)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Manual Environment Creation](#manual-environment-creation)
    - [Flow](#flow)
  - [Environment Creation Using Pipeline](#environment-creation-using-pipeline)
  - [Results](#results)

## Description

This guide describes the process of creating a new environment in the Instance repository, either manually or using an automated pipeline.

## Prerequisites

- The Instance repository already exists and follows the expected folder structure:
  
    ```plaintext
    ├── configuration
    │   ├── credentials
    │   │   ├── credentials.yml
    │   ├── config.yml
    │   ├── deployer.yml
    │   ├── registry.yml
    ├── environments
    ```

- The cluster has already been created. (Refer to the [cluster creation guide](/docs/how-to/create-cluster.md) for details.)

## Manual Environment Creation

### Flow

1. **Clone (pull updates from) the remote Instance repository to the local machine.**

2. **Create the required environment folder inside `/environments/<cluster-name>`.**
    (e.g. culster-name is example-cloud and envrionment is env-1)

    ```plaintext
    ├── environments
    │   ├── <culster-name>
    │   │   ├── <env-name>
    ```

3. **Inside the environment folder, create an `Inventory` directory:**

    ```plaintext
    ├── environments
    │   ├── <culster-name>
    │   │   ├── <env-name>
    │   │   │   ├── Inventory
    ```

    **Note:** Folder name must be `Inventory` (case-sensitive).

4. **Inside the Inventory folder, create the file `env_definition.yml`:**

    Refer to [env_definition.yml](/docs/envgene-configs.md#env_definitionyml)

    ```plaintext
    ├── environments
    │   ├── <culster-name>
    │   │   ├── <env-name>
    │   │   │   ├── Inventory
    │   │   │   │   ├── env_definition.yml
    ```

    **Note:** File name must be `env_definition.yml`.

5. **Commit and push the changes to remote repository.**

  Once you have added the necessary environment folder structure and the env_definition.yml file, commit and push the changes to the remote repository:
  
  ```bash
    git checkout -b feature/<your-feature-branch>
    git add environments/<cluster-name>/<env-name>
    git commit -m "Add new environment: <env-name> under <cluster-name>"
    git push origin feature/<your-feature-branch>
  ````

- Replace `<your-feature-branch>`, `<cluster-name>`, and `<env-name>` with appropriate values for your setup.*

## Environment Creation Using Pipeline

To create the environment using a pipeline:

- Run the pipeline with the required input parameters.
- The environment structure and inventory will be generated automatically.
See the [Environment Inventory Generation documentation](/docs/features/env-inventory-generation.md) for more details on the required parameters and behavior.

## Results

- The new environment inventory is now available in the remote Instance repository.
- If using the pipeline approach, the environment will be generated and committed automatically.

**Note:** Pass the full path `<cluster-name>/<env-name>` to the `ENV_NAMES` input parameter when executing environment operations.
