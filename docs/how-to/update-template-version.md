# Template Version Update Guide

- [Template Version Update Guide](#template-version-update-guide)
  - [Description](#description)
  - [Option 1: Manual Update via env\_definition.yml](#option-1-manual-update-via-env_definitionyml)
    - [\[Manual\] Prerequisites](#manual-prerequisites)
    - [\[Manual\] Flow](#manual-flow)
  - [Option 2: Automated Update via Pipeline Parameter](#option-2-automated-update-via-pipeline-parameter)
    - [\[Pipeline\] Prerequisites](#pipeline-prerequisites)
    - [\[Pipeline\] Flow](#pipeline-flow)
  - [Results](#results)
  - [Related Documentation](#related-documentation)

## Description

This guide provides instructions for updating the template version for an existing environment. Template version updates are necessary when:

- A new version of the Environment Template artifact has been published
- You want to apply template improvements or bug fixes to your environment

There are two approaches to update the template version:

1. **Manual update** - Direct modification of `env_definition.yml` file
2. **Pipeline parameter** - Using `ENV_TEMPLATE_VERSION` parameter when running the pipeline

---

## Option 1: Manual Update via env_definition.yml

In this approach, you manually edit the `env_definition.yml` file and update the template artifact version.

### [Manual] Prerequisites

1. The Instance Repository has already been initialized
2. The environment exists in `/environments/<cluster-name>/<environment-name>/`
3. You know the new template artifact version you want to use
4. You have access to the Instance Repository

### [Manual] Flow

1. **Clone the Instance Repository to your local machine** (if not already cloned)

   ```bash
   git clone <instance-repository-url>
   cd <instance-repository>
   ```

2. **Navigate to the Environment Inventory**

   ```bash
   cd environments/<cluster-name>/<environment-name>/Inventory
   ```

   Example:

   ```bash
   cd environments/prod-cluster/app-env/Inventory
   ```

3. **Open `env_definition.yml` for editing**

   Current content might look like:

   ```yaml
   ...
   envTemplate:
     name: composite-prod
     artifact: deployment-configuration-env-templates:1.2.3  # Old version
   ...
   ```

4. **Update the artifact version**

   Change the `envTemplate.artifact` field to the new version:

   ```yaml
   ...
   envTemplate:
     name: composite-prod
     artifact: deployment-configuration-env-templates:1.3.0  # Updated version
   ...
   ```

   > [!NOTE]
   > The artifact format is: `<artifactId>:<version>`
   > - For specific version: `my-templates:1.3.0`
   > - For SNAPSHOT (always latest): `my-templates:1.3.0-SNAPSHOT`

5. **Commit and push your changes**

   ```bash
   git add env_definition.yml
   git commit -m "Update template version to 1.3.0 for app-env"
   git push origin main
   ```

6. **Trigger the pipeline to regenerate the environment**

   Run the Instance pipeline with these parameters:

   ```text
   ENV_NAMES: prod-cluster/app-env
   ENV_BUILDER: true
   ```

   The pipeline will:
   - Download the new template version (1.3.0)
   - Regenerate all Environment Instance objects using the new template
   - Commit the changes back to the repository

---

## Option 2: Automated Update via Pipeline Parameter

In this approach, you use the `ENV_TEMPLATE_VERSION` pipeline parameter to update the template version without manually editing files.

### [Pipeline] Prerequisites

1. The Instance Repository has already been initialized
2. The environment exists in `/environments/<cluster-name>/<environment-name>/`
3. You know the new template artifact version you want to use
4. You have access to trigger the Instance pipeline (GitLab CI or GitHub Actions)

### [Pipeline] Flow

1. **Trigger the Instance pipeline with parameters**

   **For GitLab CI:**

   Navigate to: CI/CD → Pipelines → Run pipeline

   **For GitHub Actions:**

   Navigate to: Actions → Select workflow → Run workflow

   For both set parameters:

   ```text
   ENV_NAMES: prod-cluster/app-env
   ENV_BUILDER: true
   ENV_TEMPLATE_VERSION: deployment-configuration-env-templates:1.3.0
   ```

## Results

1. The `env_definition.yml` file contains the updated artifact version
2. The environment has been regenerated with the new template

---

## Related Documentation

- [Instance Pipeline Parameters](/docs/instance-pipeline-parameters.md) - Complete parameter reference
- [ENV_TEMPLATE_VERSION parameter](/docs/instance-pipeline-parameters.md#env_template_version) - Detailed parameter documentation
- [env_definition.yml structure](/docs/envgene-configs.md#env_definitionyml) - Environment Inventory format
- [Environment Instance Generation](/docs/features/environment-instance-generation.md) - How environment generation works
