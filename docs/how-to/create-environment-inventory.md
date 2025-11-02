# Environment Inventory Creation Guide

- [Environment Inventory Creation Guide](#environment-inventory-creation-guide)
  - [Description](#description)
  - [1. Manual Environment Creation](#1-manual-environment-creation)
    - [\[Manual\] Prerequisites](#manual-prerequisites)
    - [\[Manual\] Flow](#manual-flow)
  - [2. Environment Creation Using Pipeline execution](#2-environment-creation-using-pipeline-execution)
    - [\[Pipeline\] Prerequisites](#pipeline-prerequisites)
    - [\[Pipeline\] Flow](#pipeline-flow)
  - [Results](#results)

## Description

This guide provides instructions for creating a Environment Inventory in the Instance repository using two different approaches:

1. Manual Environment Creation
2. Environment Creation Using Pipeline

## 1. Manual Environment Creation

### [Manual] Prerequisites

1. The Instance repository has already been initialized and follows the required structure.

2. The cluster has already been created according to [cluster creation guide](/docs/how-to/create-cluster.md).

### [Manual] Flow

1. **Clone the Instance repository to your local machine**

2. **Create the Environment folder inside `/environments/<cluster-name>`**

    ```plaintext
    └── environments
        └── <cluster-name>
            └── <environment-name>
    ```

    Example:

    ```plaintext
    └── environments
        └── cluster-01
            └── env-1
    ```

3. **Inside the Environment folder, create an `Inventory` directory:**

    ```plaintext
    └── environments
        └── <cluster-name>
            └── <environment-name>
                └── Inventory
    ```

    Example:

    ```plaintext
    └── environments
        └── cluster-01
            └── env-1
                └── Inventory
    ```

4. **Inside the Inventory folder, create the `env_definition.yml` file:**

    ```plaintext
    └── environments
        └── <cluster-name>
            └── <env-name>
                └── Inventory
                    └── env_definition.yml
    ```

    Example:

    ```plaintext
    └── environments
        └── cluster-01
            └── env-1
                └── Inventory
                    └── env_definition.yml
    ```

    Example of simplest `env_definition.yml`

    ```yaml
    inventory:
      environmentName: string
    envTemplate:
      name: string
      artifact: string
    ```

    See details about Environment Inventory options in the [documentation](/docs/envgene-configs.md#env_definitionyml)

5. **Commit and push your changes**

## 2. Environment Creation Using Pipeline execution

### [Pipeline] Prerequisites

1. The Instance repository has already been initialized and follows the required structure.

2. The cluster has already been created according to [cluster creation guide](/docs/how-to/create-cluster.md).

### [Pipeline] Flow

1. **Trigger Instance repository pipeline with parameters:**

    ```yaml
    ENV_NAMES: "<cluster-name>/<env-name>"
    ENV_INVENTORY_INIT: "true"
    ENV_SPECIFIC_PARAMS: <...> # Optional. Used to define environment-specific parameters, or credentials
    ```

    See details about pipeline parameter options in the [documentation](/docs/instance-pipeline-parameters.md)
  
2. **The pipeline will automatically:**
   - Create the required folder structure under `/environments/<cluster-name>/<env-name>`
   - Generate the `Inventory` directory and `env_definition.yml` file
   - Optionally create:
       - Parameter Sets under `/Inventory/parameters/`
       - Credential files under `/Credentials/`
   - Commit and push the generated structure to the remote Instance repository

    > [!NOTE] You do not need to commit or push any files manually; the pipeline performs all repository operations automatically.

## Results

1. The new Environment Inventory is created in the remote Instance repository.
