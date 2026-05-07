# Application & Registry Definitions (ARD) - Use Cases

## Overview

This document defines enterprise-grade use cases for Application and Registry Definitions in EnvGene, covering sourcing, resolution, overrides, transformation, and integrations.

---

# Use Case Groups

- Template Rendering (TR)
- External Definitions (ED)
- Configuration Overrides (CO)
- Definition Resolution (DR)
- Centralized Definitions (CD)
- User Overrides (UO)
- External Consumption (EC)
- CMDB Integration (CI)
- Transformation (TF)
- Validation & Errors (VE)

---

# UC-ARD-TR-1: Basic AppDef/RegDef Template Rendering

## Pre-requisites

- Template directories exist:
  - `/templates/appdefs/appdef.yml`
  - `/templates/regdef.yml`

## Trigger

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <env_name>
ENV_BUILDER: true
```

## Steps

- `template-render` job discovers templates
- Renders:
  - `/templates/appdefs/*`
  - `/templates/regdefs/*`
- Generates AppDef and RegDef files

## Results

- AppDef and RegDef files are generated in:
  - `/genDefs/AppDefs/<appdef.yml>`
  - `/genDefs/regDefs/<regdef.yml>`

---

# UC-ARD-UO-1: Override Centralized Definitions

## Pre-requisites

- Definitions exist in:
  - `/genDefs/AppDefs/`
  - `/genDefs/regDefs/`

- User definitions exist in:
  - `/userDefs/appDefs/`
  - `/userDefs/regDefs/`

## Trigger

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <env_name>
ENV_BUILDER: true
```

## Steps

- `template-render` job discovers templates
- Renders:
  - `/templates/appdefs/*`
  - `/templates/regdefs/*`
- Generates:
  - `/genDefs/appDef/*`
  - `/genDefs/regDef/*`
- Renders:
  - `/userDefs/appDefs/*`
  - `/userDefs/regDefs/*`
- Override `/genDefs/appDef/*` and `/genDefs/regDef/*` files using definitions from:
  - `/userDefs/appDefs/*`
  - `/userDefs/regDefs/*`

## Results

- `/userDefs/appDefs/*` and `/userDefs/regDefs/*` override:
  - `/genDefs/appDef/*`
  - `/genDefs/regDef/*`

---

# UC-ARD-CI-1: Export Definitions to CMDB

## Pre-requisites

- `deployer.yml` is configured
- `inventory.deployer` is set

## Trigger

Instance pipeline (GitLab or GitHub) is started.

## Steps

- `cmdb-export` job reads:
  - `/genDefs/appDef/*`
  - `/genDefs/regDef/*`
- Pushes definitions to CMDB

## Results

- Definitions are available in CMDB

---

# UC-ARD-TR-2: Basic AppDef/RegDef Template Delete

## Pre-requisites

- Definitions exist in:
  - `/genDefs/AppDefs/*`
  - `/genDefs/regDefs/*`

- User deletes definitions from:
  - `/template/appDefs/*`
  - `/template/regDefs/*`

## Trigger

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <env_name>
ENV_BUILDER: true
```

## Steps

- `template-render` job discovers templates
- Renders changes in:
  - `/templates/appdefs/*`
  - `/templates/regdefs/*`

## Results

- No deletion is performed in:
  - `/genDefs/AppDefs/<appdef.yml>`
  - `/genDefs/regDefs/<regdef.yml>`

- Existing definitions remain unchanged even if the corresponding files are deleted from:
  - `/template/appDefs/*`
  - `/template/regDefs/*`

- Deletion of `appDef` and `regDef` definitions is currently not supported.

---

# UC-ARD-UO-2: Delete Override Definitions

## Pre-requisites

- Definitions exist in:
  - `/genDefs/AppDefs/*`
  - `/genDefs/regDefs/*`

- Override definitions exist in:
  - `/userDefs/appDefs/*`
  - `/userDefs/regDefs/*`

- User deletes definition files from:
  - `/userDefs/appDefs/*`
  - `/userDefs/regDefs/*`

## Trigger

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <env_name>
ENV_BUILDER: true
```

## Steps

- `template-render` job discovers templates
- Renders:
  - `/templates/appdefs/*`
  - `/templates/regdefs/*`
- Generates:
  - `/genDefs/appDef/*`
  - `/genDefs/regDef/*`
- Override `/genDefs/appDef/*` and `/genDefs/regDef/*` files using definitions from:
  - `/userDefs/appDefs/*`
  - `/userDefs/regDefs/*`
- Skips override operation for deleted user definition files
- Retains centralized definitions in:
  - `/genDefs/AppDefs/*`
  - `/genDefs/regDefs/*`

## Results

- No deletion is performed in:
  - `/genDefs/AppDefs/*`
  - `/genDefs/regDefs/*`

- Existing centralized definitions remain unchanged even if the corresponding override files are deleted from:
  - `/userDefs/appDefs/*`
  - `/userDefs/regDefs/*`
