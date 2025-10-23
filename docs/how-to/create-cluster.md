# Cluster Creation Guide

- [Cluster Creation Guide](#cluster-creation-guide)
  - [Description](#description)
  - [1. Creating a Cluster Without a Cloud Passport](#1-creating-a-cluster-without-a-cloud-passport)
    - [\[No Cloud Passport\] Prerequisites](#no-cloud-passport-prerequisites)
    - [\[No Cloud Passport\] Flow](#no-cloud-passport-flow)
    - [\[No Cloud Passport\] Notes](#no-cloud-passport-notes)
  - [2. Creating a Cluster With a Manually Assembled Cloud Passport](#2-creating-a-cluster-with-a-manually-assembled-cloud-passport)
    - [\[Manual Cloud Passport\] Prerequisites](#manual-cloud-passport-prerequisites)
    - [\[Manual Cloud Passport\] Flow](#manual-cloud-passport-flow)
    - [\[Manual Cloud Passport\] Notes](#manual-cloud-passport-notes)
  - [3. Creating a Cluster Using Cloud Passport Discovery](#3-creating-a-cluster-using-cloud-passport-discovery)
    - [\[Cloud Passport Discovery\] Prerequisites](#cloud-passport-discovery-prerequisites)
    - [\[Cloud Passport Discovery\] Flow](#cloud-passport-discovery-flow)
    - [\[Cloud Passport Discovery\] Notes](#cloud-passport-discovery-notes)
  - [Results](#results)

## Description

This guide provides instructions for creating a cluster in the Instance repository using three different approaches:

1. Creating a cluster without a [Cloud Passport](/docs/envgene-objects.md#cloud-passport)
2. Creating a cluster with a manually created [Cloud Passport](/docs/envgene-objects.md#cloud-passport)
3. Creating a cluster with a automatically discovered [Cloud Passport](/docs/envgene-objects.md#cloud-passport)

## 1. Creating a Cluster Without a Cloud Passport

In this approach, the [Cloud](/docs/envgene-objects.md#cloud) is generated only from the [Cloud Template](/docs/envgene-objects.md#cloud-template).

### [No Cloud Passport] Prerequisites

1. The Instance repository has already been initialized and follows the required structure.

### [No Cloud Passport] Flow

1. **Clone the Instance repository to your local machine**

2. **Create the cluster folder inside `/environments`:**

    ```plaintext
    └── environments
        └── <cluster-name>
    ```

    Example:

    ```plaintext
    └── environments
        └── cluster-01
    ```

3. **Commit and push your changes**

### [No Cloud Passport] Notes

In this approach, you must manually set the `inventory.clusterUrl` attribute in the [`env_definition.yml`](/docs/env_definition.md). This value is required because the cluster URL, protocol, and port are derived from it.

Example of `env_definition.yml`:

  ```yaml
  inventory:
    clusterUrl: https://example-cloud.example.com:443
  ```

## 2. Creating a Cluster With a Manually Assembled Cloud Passport

In this approach, the [Cloud](/docs/envgene-objects.md) is generated from the [Cloud Template](/docs/envgene-objects.md#cloud-template) and a manually assembled [Cloud Passport](/docs/envgene-objects.md#cloud-passport).

### [Manual Cloud Passport] Prerequisites

1. The Instance repository has already been initialized and follows the required structure.

### [Manual Cloud Passport] Flow

1. **Clone the Instance repository to your local machine**

2. **Create the cluster folder inside `/environments`:**

    ```plaintext
    └── environments
        └── <cluster-name>
    ```

3. **Create the Cloud Passport file manually:**

   - Collect all required parameters necessary to define the [Cloud](/docs/envgene-objects.md).
   - Assemble the [Cloud Passport](/docs/envgene-objects.md#cloud-passport) using the expected format. Refer to the sample:
     - [cluster-01.yml](/docs/samples/environments/cluster-01/cloud-passport/cluster-01.yml)
     - [cluster-01-creds.yml](/docs/samples/environments/cluster-01/cloud-passport/cluster-01-creds.yml)
   - Place it under the right location: `/environments/<cluster-name>/cloud-passport/`

   Example:

   ```plaintext
   └── environments
       └── cluster-01
           └── cloud-passport
               ├── cluster-01.yml
               └── cluster-01-creds.yml
   ```

4. **Commit and push your changes**

### [Manual Cloud Passport] Notes

In this approach, you must manually set the `inventory.cloudPassport` attribute in the [`env_definition.yml`](/docs/env_definition.md).

Example of `env_definition.yml`:

```yaml
  inventory:
    cloudPassport: cluster-01
```

## 3. Creating a Cluster Using Cloud Passport Discovery

In this approach, the [Cloud](/docs/envgene-objects.md#cloud) is generated using the [Cloud Template](/docs/envgene-objects.md#cloud-template) and a [Cloud Passport](/docs/envgene-objects.md#cloud-passport) generated automatically via discovery procedure.

### [Cloud Passport Discovery] Prerequisites

1. The Instance and Discovery repositories has already been initialized and follows the required structure.
2. Integration with Discovery repository is configured in the Instance repository:
  
    `/configuration/integration.yml`:

    ```yaml
    cp_discovery:
      gitlab:
        project: <discovery-repository>
        branch: <discovery-repository-branch>
        token: envgen.creds.get(<discovery-repository-cred-id>).secret
    ```

    `/configuration/credentials/credentials.yml`:

    ```yaml
    <discovery-repository-cred-id>:
      type: secret
      data:
        secret: <discovery-repository-token>
    ```

3. Infra namespaces in the target cluster are marked by proper labels/annotations.
4. You have [kubeconfig](https://kubernetes.io/docs/reference/config-api/kubeconfig.v1/) file for the target cluster
5. You have [Cloud Passport template](/docs/envgene-objects.md#cloud-passport-template)

### [Cloud Passport Discovery] Flow

1. **Clone the Discovery repository to your local machine**

2. **Create the cluster and environment folders inside `/environments`:**

    ```plaintext
    └── environments
        └── <cluster-name>
            └── <environment-name>
    ```

3. **Place the kubeconfig inside the cluster folder**

    ```plaintext
    └── environments
        └── <cluster-name>
            └── <environment-name>
            └── kubeconfig
    ```

    The kubeconfig file name is fixed by convention: `kubeconfig`

4. **Place the Cloud Passport template inside the environment folder**

    ```plaintext
    └── environments
        └── <cluster-name>
            ├── <environment-name>
            |   └── cloud_template.yml
            └── kubeconfig
    ```

    The Cloud Passport template file name is fixed by convention: `cloud_template.yml`

5. **Commit and push your changes**

6. **Trigger Instance repository pipeline with parameters**

    ```yaml
    ENV_NAMES: "<cluster-name>/<env-name>"
    GET_PASSPORT: "true"
    ```

    See details about pipeline parameter options in the [documentation](/docs/instance-pipeline-parameters.md)

    When this pipeline runs, Instance pipeline triggers the Discovery pipeline, which automatically generates the [Cloud Passport](/docs/envgene-objects.md#cloud-passport).

### [Cloud Passport Discovery] Notes

In this approach, you must manually set the `inventory.cloudPassport` attribute in the [`env_definition.yml`](/docs/env_definition.md).

Example of `env_definition.yml`:

   ```yaml
   inventory:
     cloudPassport: cluster-01
   ```

## Results

1. The Cloud Passport is located in the cluster folder of the Instance repository:

    ```yaml
      /environments/<cluster-name>/cloud-passport/<cluster-name>.yml
      /environments/<cluster-name>/cloud-passport/<cluster-name>-creds.yml
    ```
