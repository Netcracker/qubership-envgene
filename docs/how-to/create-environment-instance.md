# Environment Creation Guide

## Description

This guide describes the process of creating a new environment in the Instance repository.

## Prerequisites

1. **Instance Repository**
   - Ensure that the Instance repository has been created.

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

  **Note:** Pass the `<cluster-name>/<env-name>` to the ENV_NAMES input parameter when executing environment operations.

## Additional flow: Configuring integration with CMDB

### Prerequisites

1. You must know the following parameters:

- cmdb-url
- cmdb-username
- cmdb-token

### Flow

1. Clone (pull updates) remote Instance repository to the local machine  
2. Create the `app-deployer` folder at:  
    `/environments/<cluster_name>/app-deployer`  
3. Create the CMDB configuration file at:  
    `/environments/<cluster-name>/app-deployer/deployer.yml`

    **deployer.yml**

    ```yml
    app-deployer:
      username: envgen.creds.get('app-deployer-username').secret
      token: envgen.creds.get('app-deployer-token').secret
      deployerUrl: <cmdb-url>
    ```

4. Create cmdb credential configuration file at:  
    `/environments/<cloud_name>/app-deployer/deployer-creds.yml`

    **deployer-creds.yml**

    ```yml
    app-deployer-username:
      type: secret
      data:
        secret: <cmdb-username>
    app-deployer-token:
      type: secret
      data:
        secret: <cmdb-token>
    ```

5. Commit and push the update to remote repository

## Results

- Integration with CMDB is configured successfully.

## Troubleshooting

### Common Issues

1. **Pipeline Fails with authentication error**
   - Verify the access token has correct permissions.
   - Ensure the token has not expired.

2. **Missing template image**
   - Ensure you are using a valid template image configured in `env_definition.yml`.

3. **Missing deployer configuration**
   - Check deployer configuration based on `deployer` name set in `env_definition.yml`.
   - Ensure that valid CMDB credentials are being used.

### Getting Help

If you encounter issues not covered in this guide

- Check pipeline logs for error details.
- Contact the support team.
