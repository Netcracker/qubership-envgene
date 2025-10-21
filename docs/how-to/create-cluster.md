# Cluster Creation Guide

- [Cluster Creation Guide](#cluster-creation-guide)
  - [Description](#description)
  - [Creating a Cluster Without a Cloud Passport](#creating-a-cluster-without-a-cloud-passport)
    - [Prerequisites — No Cloud Passport](#prerequisites--no-cloud-passport)
    - [Flow — No Cloud Passport](#flow--no-cloud-passport)
  - [Creating a Cluster With a Manually Created Cloud Passport](#creating-a-cluster-with-a-manually-created-cloud-passport)
    - [Prerequisites — Manual Cloud Passport](#prerequisites--manual-cloud-passport)
    - [Flow — Manual Cloud Passport](#flow--manual-cloud-passport)
  - [Creating a Cluster Using Cloud Passport Discovery](#creating-a-cluster-using-cloud-passport-discovery)
    - [Prerequisites — Discovery Method](#prerequisites--discovery-method)
    - [Flow — Discovery Method](#flow--discovery-method)
  - [Results](#results)

## Description

This guide provides instructions for creating a cluster in the Instance repository using three different approaches depending on how the cloud passport is handled:

1. Creating a cluster without a **Cloud Passport**
2. Creating a cluster with a manually created **Cloud Passport**
3. Creating a cluster using **Cloud Passport Discovery**

## Creating a Cluster Without a Cloud Passport

In this approach, the **Cloud** object is generated **only from the Cloud Template**.

### Prerequisites — No Cloud Passport

- The Instance repository exists and follows the expected structure.

### Flow — No Cloud Passport

1. **Clone the Instance repository to your local machine**

2. **Create the cluster folder inside `/environments`:**

   ```plaintext
   ├── environments
   │   ├── <cluster-name>
   ```

   e.g.

     ```plaintext
     ├── environments
     │   ├── example-cloud
     ```

3. **Commit and push your changes**

> **Note:** In this approach, you must manually set the `inventory.clusterUrl` attribute in the `env_definition.yml` file under the `Inventory` directory. This value is required because the cluster URL, protocol, and port are derived from it.

Example `env_definition.yml`:

  ```yaml
  inventory:
    clusterUrl: https://example-cloud.example.com:443
  ```

## Creating a Cluster With a Manually Created Cloud Passport

In this approach, the **Cloud** object is generated from the Cloud Template and a manually assembled **Cloud Passport**.

### Prerequisites — Manual Cloud Passport

- The Instance repository exists and follows the expected structure.

### Flow — Manual Cloud Passport

1. **Clone the Instance repository to your local machine**

2. **Create the cluster folder inside `/environments`:**

   ```plaintext
   ├── environments
   │   ├── <cluster-name>
   ```

3. **Create the Cloud Passport file manually:**

   - Collect all required metadata and credentials necessary to define the Cloud environment.
   - Assemble the Cloud Passport using the expected format.
     > Refer to the sample Cloud Passport files:

     - [cluster-01.yml](/docs/samples/environments/cluster-01/cloud-passport/cluster-01.yml)

     - [cluster-01-creds.yml](/docs/samples/environments/cluster-01/cloud-passport/cluster-01-creds.yml)
   - Name the files after the cluster (e.g., `example-cloud.yml` and `example-cloud-creds.yml`).
   - Place it under the right location: `/environments/<cluster-name>/cloud-passport/`

   Example structure:

   ```plaintext
   ├── environments
   │   ├── <cluster-name>
   │   │   ├── cloud-passport
   │   │   │   ├── <cluster-name>.yml
   │   │   │   ├── <cluster-name>-creds.yml
   ```

4. **Commit and push your changes**

> **Note:** In this approach, you must manually set the `inventory.cloudPassport` attribute in the `env_definition.yml` file under the `Inventory` directory.

`env_definition.yml`:

```yaml
  inventory:
    cloudPassport: <cluster-name>
```

## Creating a Cluster Using Cloud Passport Discovery

In this approach, the **Cloud** object is generated using the Cloud Template and a Cloud Passport assembled automatically via the Discovery Pipeline. This process connects the Instance repository, Discovery repository, and the target cluster.

### Prerequisites — Discovery Method

- Ensure both the Instance and Discovery repositories exist.
- Cloud Passport repository integration is configured in the Instance repository:
  
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

- Infra Namespaces in the target cluster have correct labels/annotations.
- Ensure that the required cluster and environment structure exists in the Discovery repository along with:
  - kubeconfig file for the cluster
  - cloud_template.yml under `/environments/<cluster-name>/<env-name>/`

### Flow — Discovery Method

1. **Trigger the Pipeline in the Instance repository**
   Run the Instance repository pipeline with:

   ```bash
   ENV_NAMES=<cluster-name>/<env-name>
   ENV_BUILDER=false
   GET_PASSPORT=true
   CMDB_IMPORT=false
   ```

   **Note:** Other flag combinations may also be supported depending on your use case
  
   When this pipeline runs, `EnvGene` triggers the `Discovery Pipeline`, which automatically generates the `Cloud Passport`.
   As a result, a commit is created in the Instance repository containing the following files:

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

- The new cluster folder and Inventory configuration are created under the Instance repository.
- You can now use the cluster during environment provisioning.

**Note:** Make sure to use `<cluster-name>/<env-name>` when specifying the `ENV_NAMES` parameter during environment operations.
