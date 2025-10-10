# Simple Template Creation Guide

- [Simple Template Creation Guide](#simple-template-creation-guide)
  - [Description](#description)
  - [Prerequisites](#prerequisites)
  - [Flow](#flow)
  - [Results](#results)

## Description

This guide outlines the steps to create and register a simple environment template within the Template repository. It covers the creation of the template descriptor, associated Jinja files, and the process to build and publish the template artifact to the registry for use in environment provisioning.

## Prerequisites

- The Template repository already exists and follows the expected folder structure:

    ```plaintext
    ├── configuration
    │   ├── credentials
    │   │   ├── credentials.yml
    │   ├── deployer.yml
    │   ├── integration.yml
    ├── templates
    │   ├── env_templates
    ```

## Flow

1. **Create your folder inside `/templates/env_templates` to hold the template implementation (e.g., `simple-template`)**

    > **Note:** This folder name should match the one referenced in the template descriptor YAML file.

    - Create the following `.yml.j2` files within it:

      - [`tenant.yml.j2`](/docs/samples/templates/env_templates/composite/tenant.yml.j2)
      - [`cloud.yml.j2`](/docs/samples/templates/env_templates/composite/cloud.yml.j2)
  
2. **Create a `Namespaces` folder inside `/templates/env_templates/<template_dir>`**

3. **Inside the `Namespaces` folder, create your namespace template file with `.yml.j2` extenstion:**

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

6. **Commit and Push the Changes**

    After you’ve added the template descriptor and template files, run:

    ```bash
    git checkout -b feature/<your-feature-branch>
    git add .
    git commit -m "Add new environment template: <your-template-name>"
    git push origin feature/<your-feature-branch>
    ```

    *Replace `<your-feature-branch>` and `<your-template-name>` as appropriate.*

7. **Template Build (Automatically Triggered)**

    Once the changes are pushed to the remote repository (e.g., to the `feature/<your-feature-branch>` branch), the template build pipeline is automatically triggered.

    - Monitor the build pipeline to ensure it completes successfully.
    - Verify that the template ZIP archive is generated as expected.
    - Verify that the template builds successfully without errors during the pipeline run.
    - Verify logs from `report_artifacts` job where EnvGene displays Environment Template artifact GAV coordinates in logs like below:

      ![template_report_artifacts_logs.png](/docs/images/template_report_artifacts_logs.png)

8. **Template Publishing**

    Once the build completes successfully, the template ZIP archive is published automatically to the configured repository/registry.

    - Confirm that the template artifact is available in the correct registry location.

## Results

- The template artifact is built and published to the registry.
