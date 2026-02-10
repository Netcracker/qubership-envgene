# Simple Template Creation Guide

- [Simple Template Creation Guide](#simple-template-creation-guide)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Flow](#flow)
  - [Results](#results)

## Description

This guide outlines the steps to create and publish a simple environment template within the Template repository. It covers the creation of the template descriptor, associated Jinja files, and the process to build and publish the template artifact to the registry for use in environment provisioning.

## Prerequisites

1. The Template repository has already been initialized and follows the required structure.

## Flow

1. **Clone the Template repository to your local machine**

2. **Create folder inside `/templates/env_templates` to hold the template implementation**

    ```plaintext
    └── templates
        └── env_templates
          └── <template_dir>
    ```

    Example:

    ```plaintext
    └── templates
        └── env_templates
          └── simple
    ```

    > [!NOTE] You can choose any folder structure you like, but keep in mind two simple rules:
    >
    > 1. Every YAML file in `/templates/env_templates` is treated as a [Template Descriptor](/docs/envgene-objects.md#template-descriptor) and must match its JSON schema.
    > 2. The folder depth under `env_templates` cannot be more than 2 levels. For example:
    >
    > ```text
    > /templates/env_templates/a-folder/ - OK
    > /templates/env_templates/a-folder/b-folder - OK
    > /templates/env_templates/a-folder/b-folder/c-folder - NOT OK
    > ```

3. **Create [Tenant template](/docs/envgene-objects.md#tenant-template)**

    Example:

    [`tenant.yml.j2`](/docs/samples/template-repository/templates/env_templates/simple/tenant.yml.j2)

    ```plaintext
    └── templates
        └── env_templates
            └── simple
                └── tenant.yml.j2
    ```

4. **Create [Cloud template](/docs/envgene-objects.md#cloud-template)**

    Example:

    [`cloud.yml.j2`](/docs/samples/template-repository/templates/env_templates/simple/cloud.yml.j2)

    ```plaintext
    └── templates
        └── env_templates
            └── simple
                ├── tenant.yml.j2
                └── cloud.yml.j2
    ```

5. **Create [Namespace template](/docs/envgene-objects.md#namespace-template)**

    Example:

    [`billing.yml.j2`](/docs/samples/template-repository/templates/env_templates/simple/billing.yml.j2)

    ```plaintext
    └── templates
        └── env_templates
            └── simple
                ├── tenant.yml.j2
                ├── cloud.yml.j2
                └── billing.yml.j2
    ```

6. **Create the [Template Descriptor](/docs/envgene-objects.md#template-descriptor)**

    Example:

    [`simple.yaml`](/docs/samples/template-repository/templates/env_templates/simple.yaml)

    ```plaintext
    └── templates
        └── env_templates
            ├── simple
            |   ├── tenant.yml.j2
            |   ├── cloud.yml.j2
            |   └── billing.yml.j2
            └────── simple.yaml 
    ```

7. **Push changes and trigger the build pipeline**

8. **Find out the name and version of the Environment Template**

   - After pushing your changes the template build pipeline is triggered automatically.
   - On successful execution, the pipeline build and publish Environment Template as Maven artifact.
   - To find out the name and version of the artifact, check the `report_artifacts` job logs:
  
       ```plaintext
       
       SNAPSHOT version
       ======================================================================
       
       envTemplate:
         artifact: <env-template-artifact-id>:<env-template-version-SNAPSHOT>
       ======================================================================
       
       Concrete version
       ======================================================================
       
       envTemplate:
         artifact: <env-template-artifact-id>:<env-template-version>
       ======================================================================
       
       Link to download zip part of the artifact template
       ======================================================================
       
       <link-to-zip-part-of-artifact>
       ======================================================================
       ```  

      > [!NOTE] SNAPSHOT version means that Environment Instance will always use the latest template version, and it will not be necessary to change it during Environment Instance generation each time after new version of Environment Template is published.

## Results

1. The Environment template artifact is built and published to the registry for use in Environment Instance generation.
