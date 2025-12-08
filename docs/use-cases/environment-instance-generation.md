# Environment Instance Generation Use Cases

- [Environment Instance Generation Use Cases](#environment-instance-generation-use-cases)
  - [Overview](#overview)
  - [Namespace Folder Name Generation](#namespace-folder-name-generation)
    - [UC-EIG-NF-1: Namespace NOT in BG Domain with deploy\_postfix](#uc-eig-nf-1-namespace-not-in-bg-domain-with-deploy_postfix)
    - [UC-EIG-NF-2: Namespace NOT in BG Domain without deploy\_postfix](#uc-eig-nf-2-namespace-not-in-bg-domain-without-deploy_postfix)
    - [UC-EIG-NF-3: Controller Namespace in BG Domain with deploy\_postfix](#uc-eig-nf-3-controller-namespace-in-bg-domain-with-deploy_postfix)
    - [UC-EIG-NF-4: Controller Namespace in BG Domain without deploy\_postfix](#uc-eig-nf-4-controller-namespace-in-bg-domain-without-deploy_postfix)
    - [UC-EIG-NF-5: Origin Namespace in BG Domain with deploy\_postfix](#uc-eig-nf-5-origin-namespace-in-bg-domain-with-deploy_postfix)
    - [UC-EIG-NF-6: Origin Namespace in BG Domain without deploy\_postfix](#uc-eig-nf-6-origin-namespace-in-bg-domain-without-deploy_postfix)
    - [UC-EIG-NF-7: Peer Namespace in BG Domain with deploy\_postfix](#uc-eig-nf-7-peer-namespace-in-bg-domain-with-deploy_postfix)
    - [UC-EIG-NF-8: Peer Namespace in BG Domain without deploy\_postfix](#uc-eig-nf-8-peer-namespace-in-bg-domain-without-deploy_postfix)
  - [Template Artifacts Selection](#template-artifacts-selection)
    - [UC-EIG-TA-1: Environment Instance Generation with Common Artifact Only](#uc-eig-ta-1-environment-instance-generation-with-common-artifact-only)
    - [UC-EIG-TA-2: Environment Instance Generation with Blue-Green Artifacts](#uc-eig-ta-2-environment-instance-generation-with-blue-green-artifacts)
    - [UC-EIG-TA-3: Environment Instance Generation with Mixed Artifacts (BG and Non-BG Namespaces)](#uc-eig-ta-3-environment-instance-generation-with-mixed-artifacts-bg-and-non-bg-namespaces)

## Overview

This document covers use cases for [Environment Instance Generation](/docs/features/environment-instance-generation.md) - the process of creating Environment Instance objects from Environment Templates.

## Namespace Folder Name Generation

The folder name generation logic depends on whether the namespace is part of a BG Domain, the namespace's BG role (origin, peer, or controller), and whether `deploy_postfix` is specified in the Template Descriptor. The resulting folder name defines the path structure: `/environments/<cluster-name>/<env-name>/Namespaces/<folder-name>/`.

### UC-EIG-NF-1: Namespace NOT in BG Domain with deploy_postfix

**Pre-requisites:**

1. Environment Inventory exists
2. Environment Template contains a Namespace template
3. Namespace is **not** part of a BG Domain
4. Template Descriptor specifies `deploy_postfix` for this Namespace:

   ```yaml
   namespaces:
     - template_path: "templates/env_templates/dev/Namespaces/core.yml.j2"
       deploy_postfix: "core"
   ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_builder` job runs in the pipeline:
   1. Reads Environment Template and Template Descriptor
   2. Identifies that Namespace is not part of BG Domain
   3. Finds `deploy_postfix: "core"` in Template Descriptor
   4. Generates folder name using `deploy_postfix` value

**Results:**

1. Namespace folder is created at: `/environments/<cluster-name>/<env-name>/Namespaces/core/`
2. Folder name equals `deploy_postfix` value: `core`
3. Namespace object is placed in the `core` folder

### UC-EIG-NF-2: Namespace NOT in BG Domain without deploy_postfix

**Pre-requisites:**

1. Environment Inventory exists
2. Environment Template contains a Namespace template
3. Namespace is **not** part of a BG Domain
4. Template Descriptor does **not** specify `deploy_postfix` for this Namespace:

   ```yaml
   namespaces:
     - template_path: "templates/env_templates/dev/Namespaces/bss.yml.j2"
       # deploy_postfix is not specified
   ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_builder` job runs in the pipeline:
   1. Reads Environment Template and Template Descriptor
   2. Identifies that Namespace is not part of BG Domain
   3. Does not find `deploy_postfix` in Template Descriptor
   4. Extracts namespace template filename: `bss.yml.j2`
   5. Removes extension to get template name: `bss`
   6. Generates folder name using template name

**Results:**

1. Namespace folder is created at: `/environments/<cluster-name>/<env-name>/Namespaces/bss/`
2. Folder name equals namespace template name (without extension): `bss`
3. Namespace object is placed in the `bss` folder

### UC-EIG-NF-3: Controller Namespace in BG Domain with deploy_postfix

**Pre-requisites:**

1. Environment Inventory exists
2. Environment Instance contains BG Domain object
3. Namespace is part of BG Domain with role `controller`
4. Template Descriptor specifies `deploy_postfix` for this Namespace:

   ```yaml
   namespaces:
     - template_path: "templates/env_templates/dev/Namespaces/controller.yml.j2"
       deploy_postfix: "controller"
   ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_builder` job runs in the pipeline:
   1. Reads Environment Template and Template Descriptor
   2. Identifies that Namespace is part of BG Domain with role `controller`
   3. Applies rules for controller namespace (same as non-BG namespaces)
   4. Finds `deploy_postfix: "controller"` in Template Descriptor
   5. Generates folder name using `deploy_postfix` value (no suffix added)

**Results:**

1. Namespace folder is created at: `/environments/<cluster-name>/<env-name>/Namespaces/controller/`
2. Folder name equals `deploy_postfix` value: `controller` (no `-controller` suffix)
3. Namespace object is placed in the `controller` folder

### UC-EIG-NF-4: Controller Namespace in BG Domain without deploy_postfix

**Pre-requisites:**

1. Environment Inventory exists
2. Environment Instance contains BG Domain object
3. Namespace is part of BG Domain with role `controller`
4. Template Descriptor does **not** specify `deploy_postfix` for this Namespace:

   ```yaml
   namespaces:
     - template_path: "templates/env_templates/dev/Namespaces/controller.yml.j2"
       # deploy_postfix is not specified
   ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_builder` job runs in the pipeline:
   1. Reads Environment Template and Template Descriptor
   2. Identifies that Namespace is part of BG Domain with role `controller`
   3. Applies rules for controller namespace (same as non-BG namespaces)
   4. Does not find `deploy_postfix` in Template Descriptor
   5. Extracts namespace template filename: `controller.yml.j2`
   6. Removes extension to get template name: `controller`
   7. Generates folder name using template name (no suffix added)

**Results:**

1. Namespace folder is created at: `/environments/<cluster-name>/<env-name>/Namespaces/controller/`
2. Folder name equals namespace template name: `controller` (no `-controller` suffix)
3. Namespace object is placed in the `controller` folder

### UC-EIG-NF-5: Origin Namespace in BG Domain with deploy_postfix

**Pre-requisites:**

1. Environment Inventory exists
2. Environment Instance contains BG Domain object
3. Namespace is part of BG Domain with role `origin`
4. Template Descriptor specifies `deploy_postfix` for this Namespace:

   ```yaml
   namespaces:
     - template_path: "templates/env_templates/dev/Namespaces/bss.yml.j2"
       deploy_postfix: "bss"
   ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_builder` job runs in the pipeline:
   1. Reads Environment Template and Template Descriptor
   2. Identifies that Namespace is part of BG Domain with role `origin`
   3. Finds `deploy_postfix: "bss"` in Template Descriptor
   4. Appends BG role suffix `-origin` to `deploy_postfix`
   5. Generates folder name: `bss-origin`

**Results:**

1. Namespace folder is created at: `/environments/<cluster-name>/<env-name>/Namespaces/bss-origin/`
2. Folder name equals `deploy_postfix` + `-origin` suffix: `bss-origin`
3. Namespace object is placed in the `bss-origin` folder

### UC-EIG-NF-6: Origin Namespace in BG Domain without deploy_postfix

**Pre-requisites:**

1. Environment Inventory exists
2. Environment Instance contains BG Domain object
3. Namespace is part of BG Domain with role `origin`
4. Template Descriptor does **not** specify `deploy_postfix` for this Namespace:

   ```yaml
   namespaces:
     - template_path: "templates/env_templates/dev/Namespaces/bss.yml.j2"
       # deploy_postfix is not specified
   ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_builder` job runs in the pipeline:
   1. Reads Environment Template and Template Descriptor
   2. Identifies that Namespace is part of BG Domain with role `origin`
   3. Does not find `deploy_postfix` in Template Descriptor
   4. Extracts namespace template filename: `bss.yml.j2`
   5. Removes extension to get template name: `bss`
   6. Appends BG role suffix `-origin` to template name
   7. Generates folder name: `bss-origin`

**Results:**

1. Namespace folder is created at: `/environments/<cluster-name>/<env-name>/Namespaces/bss-origin/`
2. Folder name equals namespace template name + `-origin` suffix: `bss-origin`
3. Namespace object is placed in the `bss-origin` folder

### UC-EIG-NF-7: Peer Namespace in BG Domain with deploy_postfix

**Pre-requisites:**

1. Environment Inventory exists
2. Environment Instance contains BG Domain object
3. Namespace is part of BG Domain with role `peer`
4. Template Descriptor specifies `deploy_postfix` for this Namespace:

   ```yaml
   namespaces:
     - template_path: "templates/env_templates/dev/Namespaces/bss.yml.j2"
       deploy_postfix: "bss"
   ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_builder` job runs in the pipeline:
   1. Reads Environment Template and Template Descriptor
   2. Identifies that Namespace is part of BG Domain with role `peer`
   3. Finds `deploy_postfix: "bss"` in Template Descriptor
   4. Appends BG role suffix `-peer` to `deploy_postfix`
   5. Generates folder name: `bss-peer`

**Results:**

1. Namespace folder is created at: `/environments/<cluster-name>/<env-name>/Namespaces/bss-peer/`
2. Folder name equals `deploy_postfix` + `-peer` suffix: `bss-peer`
3. Namespace object is placed in the `bss-peer` folder

### UC-EIG-NF-8: Peer Namespace in BG Domain without deploy_postfix

**Pre-requisites:**

1. Environment Inventory exists
2. Environment Instance contains BG Domain object
3. Namespace is part of BG Domain with role `peer`
4. Template Descriptor does **not** specify `deploy_postfix` for this Namespace:

   ```yaml
   namespaces:
     - template_path: "templates/env_templates/dev/Namespaces/bss.yml.j2"
       # deploy_postfix is not specified
   ```

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_builder` job runs in the pipeline:
   1. Reads Environment Template and Template Descriptor
   2. Identifies that Namespace is part of BG Domain with role `peer`
   3. Does not find `deploy_postfix` in Template Descriptor
   4. Extracts namespace template filename: `bss.yml.j2`
   5. Removes extension to get template name: `bss`
   6. Appends BG role suffix `-peer` to template name
   7. Generates folder name: `bss-peer`

**Results:**

1. Namespace folder is created at: `/environments/<cluster-name>/<env-name>/Namespaces/bss-peer/`
2. Folder name equals namespace template name + `-peer` suffix: `bss-peer`
3. Namespace object is placed in the `bss-peer` folder

## Template Artifacts Selection

The artifact selection logic depends on whether Blue-Green artifacts are specified in the Environment Inventory and the role of the namespace being rendered (origin, peer, controller, or non-BG). It determines which template artifact version is used for rendering objects in the Environment Instance.

### UC-EIG-TA-1: Environment Instance Generation with Common Artifact Only

**Pre-requisites:**

1. Environment Inventory exists with only `envTemplate.artifact` specified (no `bgArtifacts`):

   ```yaml
   envTemplate:
     name: "composite-prod"
     artifact: "project-env-template:v1.2.3"
   ```

2. Environment Instance may or may not contain BG Domain object
3. Template artifact is available

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_builder` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Identifies that only `envTemplate.artifact` is specified
   3. Uses `envTemplate.artifact` for rendering all Environment Instance objects:
      - All Namespaces (including `origin`, `peer`, `controller` if present in BG Domain)
      - Tenant, Cloud, Applications, Resource Profiles, Credentials, and all other objects

**Results:**

1. All Namespaces are rendered using `project-env-template:v1.2.3`
2. All other objects (Tenant, Cloud, Applications, etc.) are rendered using `project-env-template:v1.2.3`
3. Environment Instance is generated with consistent artifact usage across all objects

### UC-EIG-TA-2: Environment Instance Generation with Blue-Green Artifacts

**Pre-requisites:**

1. Environment Inventory exists with both `envTemplate.artifact` and `envTemplate.bgArtifacts` specified:

   ```yaml
   envTemplate:
     name: "composite-prod"
     artifact: "project-env-template:v1.2.3"
     bgArtifacts:
       origin: "project-env-template:v1.2.3-origin"
       peer: "project-env-template:v1.2.3-peer"
   ```

2. Environment Instance contains BG Domain object with `origin` and `peer` namespaces
3. Template artifacts specified in `bgArtifacts` are available

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_builder` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Reads BG Domain object to determine namespace roles
   3. For `origin` Namespace: Uses `envTemplate.bgArtifacts.origin` artifact
   4. For `peer` Namespace: Uses `envTemplate.bgArtifacts.peer` artifact
   5. For `controller` Namespace: Uses `envTemplate.artifact` artifact
   6. For all other objects: Uses `envTemplate.artifact` artifact

**Results:**

1. `origin` Namespace is rendered using `project-env-template:v1.2.3-origin`
2. `peer` Namespace is rendered using `project-env-template:v1.2.3-peer`
3. `controller` Namespace is rendered using `project-env-template:v1.2.3`
4. All other objects (Tenant, Cloud, Applications, etc.) are rendered using `project-env-template:v1.2.3`
5. Environment Instance is generated with correct artifact assignments based on namespace roles

### UC-EIG-TA-3: Environment Instance Generation with Mixed Artifacts (BG and Non-BG Namespaces)

**Pre-requisites:**

1. Environment Inventory exists with both `envTemplate.artifact` and `envTemplate.bgArtifacts` specified:

   ```yaml
   envTemplate:
     name: "composite-prod"
     artifact: "project-env-template:v1.2.3"
     bgArtifacts:
       origin: "project-env-template:v1.2.3-origin"
       peer: "project-env-template:v1.2.3-peer"
   ```

2. Environment Instance contains BG Domain object with `origin`, `peer`, and `controller` namespaces
3. Environment Instance contains additional namespaces not part of BG Domain (e.g., `core`, `api`)
4. Template artifacts are available

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

1. `ENV_NAMES: <env_name>`
2. `ENV_BUILDER: true`

**Steps:**

1. The `env_builder` job runs in the pipeline:
   1. Reads Environment Inventory
   2. Reads BG Domain object to determine namespace roles
   3. For `origin` Namespace: Uses `envTemplate.bgArtifacts.origin` artifact
   4. For `peer` Namespace: Uses `envTemplate.bgArtifacts.peer` artifact
   5. For `controller` Namespace: Uses `envTemplate.artifact` artifact
   6. For non-BG namespaces (`core`, `api`): Uses `envTemplate.artifact` artifact
   7. For all other objects: Uses `envTemplate.artifact` artifact

**Results:**

1. `origin` Namespace is rendered using `project-env-template:v1.2.3-origin`
2. `peer` Namespace is rendered using `project-env-template:v1.2.3-peer`
3. `controller` Namespace is rendered using `project-env-template:v1.2.3`
4. Non-BG namespaces (`core`, `api`) are rendered using `project-env-template:v1.2.3`
5. All other objects (Tenant, Cloud, Applications, etc.) are rendered using `project-env-template:v1.2.3`
6. Environment Instance is generated with correct artifact assignments:
   - BG-specific artifacts for `origin` and `peer` namespaces
   - Common artifact for all other namespaces and objects
