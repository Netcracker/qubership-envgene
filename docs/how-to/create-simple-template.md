# Simple Template Creation Guide

- [Simple Template Creation Guide](#simple-template-creation-guide)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Flow](#flow)
  - [Results](#results)

## Description

This guide outlines the steps to create and register a simple environment template within the Template repository. It covers the creation of the template descriptor, associated Jinja files, and the process to build and publish the template artifact to the registry for use in environment provisioning.

## Prerequisites

- The Template repository has already been initialized and follows the standard structure.

## Flow

1. **Create your folder inside `/templates/env_templates` to hold the template implementation (e.g., `simple-template`)**

    > **Note:** This folder name should match the one referenced in the template descriptor YAML file.

    - Create the following `.yml.j2` files within it:

      - [`tenant.yml.j2`](/docs/samples/templates/env_templates/composite/tenant.yml.j2)
      - [`cloud.yml.j2`](/docs/samples/templates/env_templates/composite/cloud.yml.j2)
  
2. **Create a `Namespaces` folder inside `/templates/env_templates/<template_dir>`**

3. **Inside the `Namespaces` folder, create your namespace template file with `.yml.j2` extension:**

    - e.g. [`core.yml.j2`](/docs/samples/templates/env_templates/composite/namespaces/core.yml.j2)
  
4. **Create a template descriptor YAML file (e.g., `<my-template>.yaml`)**

    - Place this file inside the `/templates/env_templates` directory in the template repository with the following content:

      ```yaml
      tenant: "{{ templates_dir }}/env_templates/<template_dir>/tenant.yml.j2"
      cloud: "{{ templates_dir }}/env_templates/<template_dir>/cloud.yml.j2"
      namespaces:
        - template_path: "{{ templates_dir }}/env_templates/<template_dir>/Namespaces/core.yml.j2"
      ```

    - This file describes the overall template structure: Tenant, Cloud, Namespaces, etc.

5. **The final template repository should have the following structure:**

    ```plaintext
    ├── templates
    │   ├── env_templates
    │   │   ├── <my-template>.yaml
    │   │   ├── <template_dir>
    │   │   │   ├── Namespaces
    │   │   │   │   ├── core.yml.j2
    │   │   │   ├── cloud.yml.j2
    │   │   │   ├── tenant.yml.j2
    ```

6. **Push changes and trigger the build pipeline**

   - After pushing your changes to a feature branch, the template build pipeline is triggered automatically.
   - On successful execution, the pipeline generates the template ZIP archive and publishes it to the configured registry.
   - During the build, verify the `report_artifacts` job in the logs to locate the Environment Template artifact GAV coordinates. The output will be in the following format:
  
       ```plaintext
         
      To use the built artifact in GAV notation, set the following in the Environment Inventory:
       SNAPSHOT version
       ======================================================================
       
       envTemplate:
         artifact:
           group_id: <env-template-group-id>
           artifact_id: <env-template-artifact-id>
           version: <env-template-version-SNAPSHOT>
       ======================================================================
       
       Concrete version
       ======================================================================
       
       envTemplate:
         artifact:
           group_id: <env-template-group-id>
           artifact_id: <env-template-artifact-id>
           version: <env-template-version>
       ======================================================================
       
       To use the built artifact in application:version notation, set the following in the Environment Inventory:
       
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
       
       NOTE: The applicationDefinition with the name <env-template-artifact-id> must be created in the cloud CMDB (cloud-deployer) for using app:ver notation
       
       Link to download zip part of the artifact template
       ======================================================================
       
       <link-to-zip-part-of-artifact>
       ======================================================================
       ```  

      > **Note:** SNAPSHOT version means that Environment Instance will always use the latest template version, and it will not be necessary to change it during Environment Instance generation each time after new version of Environment Template is published.

## Results

- The environment template artifact is built and published to the registry for use in environment provisioning.
