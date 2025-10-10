# Cluster Creation Guide

- [Cluster Creation Guide](#cluster-creation-guide)
  - [Description](#description)
  - [Creating a Cluster Without a Cloud Passport](#creating-a-cluster-without-a-cloud-passport)
    - [Prerequisites](#prerequisites)
    - [Flow](#flow)
  - [Creating a Cluster With a Manually Created Cloud Passport](#creating-a-cluster-with-a-manually-created-cloud-passport)
    - [Prerequisites](#prerequisites-1)
    - [Flow](#flow-1)
  - [Creating a Cluster Using Cloud Passport Discovery](#creating-a-cluster-using-cloud-passport-discovery)
    - [Prerequisites](#prerequisites-2)
    - [Flow](#flow-2)
  - [Results](#results)

## Description

This guide provides instructions for creating a cluster in the Instance repository using three different approaches depending on how the cloud passport is handled:

1. Creating a cluster without a cloud passport
2. Creating a Cluster With a Manually Created Cloud Passport
3. Creating a Cluster Using Cloud Passport Discovery

## Creating a Cluster Without a Cloud Passport

In this approach, the cloud object is generated **only from the cloud template**.

### Prerequisites

- The Instance repository must exist and follow the expected structure.

### Flow

1. Clone the Instance repository to your local machine

2. Create the cluster folder inside `/environments`:

   ```plaintext
   ├── environments
   │   ├── <cluster-name>
   ```

   e.g.

     ```plaintext
     ├── environments
     │   ├── example-cloud
     ```

3. Commit and push the changes:

   ```bash
   git checkout -b feature/create-example-cloud
   git add environments/example-cloud
   git commit -m "Create cluster: example-cloud (without passport)"
   git push origin feature/create-example-cloud
   ```

> **Note:** In this approach, you must manually set the `inventory.clusterUrl` attribute in the `env_definition.yml` file under the `Inventory` directory.  
> This value is required because the cluster URL, protocol, and port are derived from it.

Example `env_definition.yml`:

  ```yaml
  inventory:
    clusterUrl: https://example-cloud.example.com:443
  ```

## Creating a Cluster With a Manually Created Cloud Passport

In this approach, the cloud object is generated from the cloud template and a manually assembled cloud passport.

### Prerequisites

- The Instance repository must exist and follow the expected structure

### Flow

1. Clone the Instance repository to your local machine

2. Create the cluster folder inside `/environments`:

   ```plaintext
   ├── environments
   │   ├── <cluster-name>
   ```

3. Create the cloud passport file manually:

   - Collect all required metadata and credentials necessary to define the cloud environment
        - refer sample [cluster-01.yml](/docs/samples/environments/cluster-01/cloud-passport/cluster-01.yml)
        - refer sample [cluster-01-creds.yml](/docs/samples/environments/cluster-01/cloud-passport/cluster-01-creds.yml)
   - Assemble the cloud passport using the expected format
   - Name the file after the cluster (e.g., `example-cloud.yml`)
   - Place it under the right location: `/environments/<cluster-name>/cloud-passport/`

   Example structure:

   ```plaintext
   ├── environments
   │   ├── <cluster-name>
   │   │   ├── cloud-passport
   │   │   │   ├── <cluster-name>.yml
   │   │   │   ├── <cluster-name>-creds.yml
   ```

4. Commit and push the changes:

   ```bash
   git checkout -b feature/create-example-cloud
   git add environments/example-cloud
   git add configuration/credentials/cloud-passports/example-cloud.yml
   git commit -m "Create cluster with manual cloud passport: example-cloud"
   git push origin feature/create-example-cloud
   ```

> **Note:** In this approach, you must manually set the `inventory.cloudPassport` attribute in the `env_definition.yml` file under the `Inventory` directory.

`env_definition.yml`:

```yaml
  inventory:
    cloudPassport: <cluster-name>
```

## Creating a Cluster Using Cloud Passport Discovery

In this approach, the cloud object is generated using the cloud template and a cloud passport assembled automatically via the Discovery pipeline. This process connects the Instance repository, Discovery repository, and the target cluster.

### Prerequisites

- Ensure both the Instance and Discovery repositories exist
- Verify the target namespaces in your cluster are correctly labeled

### Flow

1. Configure Integration with the Discovery Repository

   Ensure the following configuration is present in the Instance repository:

   In `/configuration/integration.yml`:

   ```yaml
   cp_discovery:
     gitlab:
       project: <discovery-repository>
       branch: <discovery-repository-branch>
       token: envgen.creds.get(<discovery-repository-cred-id>).secret
   ```

   In `/configuration/credentials/credentials.yml`:

   ```yaml
   discovery-repository-cred-id:
     type: "secret"
     data:
       secret: <discovery-repository-token>
   ```

2. Trigger the pipeline in the Instance repository with the following parameters:

   ```bash
   ENV_NAMES=<cluster-name>/<env-name>
   ENV_BUILDER=false
   GET_PASSPORT=true
   CMDB_IMPORT=false
   ```

   Note: Other flag combinations may also be supported depending on your use case
  
   **Internal working of discovery pipeline:**

   EnvGene triggers the Discovery pipeline, which internally executes the Discovery CLI.The Discovery CLI performs the following actions internally:

    - Connects to the cluster using the kubeconfig file located at: `/environments/<cluster-name>/kubeconfig`

    - Reads the cloud template from: `/environments/<cluster-name>/<env-name>/cloud_template.yml`
    - Utilizes the SECRET_KEY CI/CD variable for encrypting data
    - Discovers cloud-related resources from the cluster
    - Generates the following files:
        - cloud-passport.yml
        - cloud-passport-creds.yml
    - Encrypts the credentials file using a SECRET_KEY
    - Returns both the generated files and encryption metadata back to EnvGene

   EnvGene processes the received Cloud Passport:

    - Receives the encrypted files and metadata
    - Requests the Fernet key from the Discovery repository
    - Decrypts the credentials file using the Discovery key
    - Re-encrypts the credentials using the local SECRET_KEY

   Decryption Mode (optional):
   Based on `/configuration/config.yml`:

    ```yaml
      cloud_passport_decryption: true  # or false
    ```

    - If set to true: The system attempts decryption using the local SECRET_KEY
    - If not set or false: Skips decryption, commits encrypted credentials as-is
  
   EnvGene commits the following files to the Instance repository:

    ```yaml
      /environments/<cluster-name>/cloud-passport/<cluster-name>.yml
      /environments/<cluster-name>/cloud-passport/<cluster-name>-creds.yml
    ```

> **Note:** In this approach, you must manually set the `inventory.cloudPassport` attribute in the `env_definition.yml` file under the `Inventory` directory.

 `env_definition.yml`:

   ```yaml
   inventory:
     cloudPassport: <cluster-name>
   ```

## Results

- The new cluster folder and inventory configuration are created under the Instance repository.
- You can now use the cluster during environment provisioning.

**Note:** Make sure to use `<cluster-name>/<env-name>` when specifying the `ENV_NAMES` parameter during environment operations.
