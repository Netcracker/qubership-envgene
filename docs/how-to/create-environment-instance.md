# Environment Creation Guide

## Description

This guide describes the process of creating a new environment in the Instance repository.

## Prerequisites

1. **Instance Repository**
   - Ensure that the Instance repository has been created with following folder structure:

    ```plaintext
    ├── configuration
    │   ├── credentials
    │   │   ├── credentials.yml
    │   ├── config.yml
    │   ├── deployer.yml
    │   ├── registry.yml
    ├── environments
    ```

## Flow

1. **Clone (pull updates) the remote Instance repository to the local machine.**

2. **Create the Cluster folder inside /environments**  
   Refer to [how to create cluster](create-cluster.md)

    ```plaintext
    |_ environments
       |_ example-cloud
    ```

3. **Create required environment folder inside - `/environments/<example_cloud>`**

    ```plaintext
    |_environments
      |_example-cloud
        |_env-1
    ```

4. **Create an inventory folder named `Inventory` inside - `/environments/<example_cloud>/<env-1>`**

    ```plaintext
    |_environments
      |_example-cloud
        |_env-1
          |_Inventory
    ```

    **Note:** Folder name must be `Inventory` (case-sensitive).

5. **Create the inventory file named `env_definition.yml` inside - `/environments/<example_cloud>/<env-1>/Inventory`**

    Refer to [env_definitionyml](../envgene-configs.md#env_definitionyml)

    ```plaintext
    |_environments
      |_example-cloud
        |_env-1
          |_Inventory
            |_env_definition.yml
    ```

    **Note:** File name must be `env_definition.yml`.

6. **Commit and push the update to remote repository.**

## Results

The environment inventory is now available in the remote Instance repository.

  **Note:** Pass the `<cluster-name>/<env-name>` to the `ENV_NAMES` input parameter when executing environment operations.
