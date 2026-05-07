# Application & Registry Definitions Use Cases

- [Application & Registry Definitions Use Cases](#application--registry-definitions-use-cases)
  - [Overview](#overview)
  - [Use Case Groups](#use-case-groups)
    - [Template Rendering](#template-rendering)
      - [UC-ARD-TR-1: Basic AppDef/RegDef Template Rendering](#uc-ard-tr-1-basic-appdefregdef-template-rendering)
      - [UC-ARD-TR-2: Basic AppDef/RegDef Template Delete](#uc-ard-tr-2-basic-appdefregdef-template-delete)
    - [User Overrides](#user-overrides)
      - [UC-ARD-UO-1: Override Centralized Definitions](#uc-ard-uo-1-override-centralized-definitions)
      - [UC-ARD-UO-2: Delete Override Definitions](#uc-ard-uo-2-delete-override-definitions)
    - [CMDB Integration](#cmdb-integration)
      - [UC-ARD-CI-1: Export Definitions to CMDB](#uc-ard-ci-1-export-definitions-to-cmdb)

## Overview

This document defines use cases for Application Definitions (AppDef) and Registry Definitions (RegDef) in EnvGene.

The use cases cover:

1. Template rendering
2. Centralized definition generation
3. User override processing
4. Definition persistence behavior
5. CMDB integration
6. Definition lifecycle handling

## Use Case Groups

This document is organized into the following functional groups:

| Group | Description |
|---|---|
| Template Rendering (TR) | Generation of AppDef and RegDef objects from templates |
| User Overrides (UO) | Override processing using user-provided definitions |
| CMDB Integration (CI) | Export and synchronization of definitions to CMDB systems |

## Template Rendering

This group covers rendering and generation of centralized Application Definitions and Registry Definitions from templates.

### UC-ARD-TR-1: Basic AppDef/RegDef Template Rendering

**Pre-requisites:**

1. Template directories exist:
   - `/templates/appdefs/appdef.yml`
   - `/templates/regdefs/regdef.yml`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <env_name>
ENV_BUILDER: true
```

**Steps:**

1. The `template-render` job runs in the pipeline:
   1. Discovers template definition files
   2. Renders templates from:
      - `/templates/appdefs/*`
      - `/templates/regdefs/*`
   3. Generates centralized definitions into:
      - `/genDefs/appDefs/*`
      - `/genDefs/regDefs/*`

**Results:**

1. Application Definitions are generated in:
   - `/genDefs/appDefs/<appdef.yml>`
2. Registry Definitions are generated in:
   - `/genDefs/regDefs/<regdef.yml>`
3. Generated definitions become available for downstream pipeline processing

### UC-ARD-TR-2: Basic AppDef/RegDef Template Delete

**Pre-requisites:**

1. Definitions already exist in:
   - `/genDefs/appDefs/*`
   - `/genDefs/regDefs/*`

2. User removes template files from:
   - `/templates/appdefs/*`
   - `/templates/regdefs/*`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <env_name>
ENV_BUILDER: true
```

**Steps:**

1. The `template-render` job runs in the pipeline:
   1. Discovers current template definition files
   2. Detects deleted template files
   3. Renders existing templates from:
      - `/templates/appdefs/*`
      - `/templates/regdefs/*`
   4. Skips deletion of previously generated centralized definitions

**Results:**

1. No deletion is performed in:
   - `/genDefs/appDefs/*`
   - `/genDefs/regDefs/*`
2. Existing centralized definitions remain unchanged even when corresponding template files are deleted
3. Deletion of generated AppDef and RegDef objects is currently not supported

## User Overrides

This group covers override functionality where user-provided definitions supersede centralized generated definitions.

### UC-ARD-UO-1: Override Centralized Definitions

**Pre-requisites:**

1. Centralized definitions exist in:
   - `/genDefs/appDefs/*`
   - `/genDefs/regDefs/*`

2. User override definitions exist in:
   - `/userDefs/appDefs/*`
   - `/userDefs/regDefs/*`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <env_name>
ENV_BUILDER: true
```

**Steps:**

1. The `template-render` job runs in the pipeline:
   1. Discovers template definition files
   2. Renders templates from:
      - `/templates/appdefs/*`
      - `/templates/regdefs/*`
   3. Generates centralized definitions into:
      - `/genDefs/appDefs/*`
      - `/genDefs/regDefs/*`
   4. Discovers user override definitions from:
      - `/userDefs/appDefs/*`
      - `/userDefs/regDefs/*`
   5. Overrides centralized definitions using user-provided definitions

**Results:**

1. Definitions from:
   - `/userDefs/appDefs/*`
   - `/userDefs/regDefs/*`
   override generated definitions from:
   - `/genDefs/appDefs/*`
   - `/genDefs/regDefs/*`
2. User-provided definitions take precedence during downstream processing
3. Final effective definitions contain overridden user configuration

### UC-ARD-UO-2: Delete Override Definitions

**Pre-requisites:**

1. Centralized definitions exist in:
   - `/genDefs/appDefs/*`
   - `/genDefs/regDefs/*`

2. Override definitions previously existed in:
   - `/userDefs/appDefs/*`
   - `/userDefs/regDefs/*`

3. User deletes override files from:
   - `/userDefs/appDefs/*`
   - `/userDefs/regDefs/*`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <env_name>
ENV_BUILDER: true
```

**Steps:**

1. The `template-render` job runs in the pipeline:
   1. Discovers template definition files
   2. Renders templates from:
      - `/templates/appdefs/*`
      - `/templates/regdefs/*`
   3. Generates centralized definitions into:
      - `/genDefs/appDefs/*`
      - `/genDefs/regDefs/*`
   4. Detects deleted override definition files
   5. Skips override processing for deleted override files
   6. Retains centralized generated definitions as effective definitions

**Results:**

1. No deletion is performed in:
   - `/genDefs/appDefs/*`
   - `/genDefs/regDefs/*`
2. Existing centralized definitions remain active when override files are deleted
3. Effective definitions revert back to centralized generated definitions
4. Deletion of override files only removes override behavior and does not delete centralized definitions

## CMDB Integration

This group covers integration and synchronization of Application Definitions and Registry Definitions with external CMDB systems.

### UC-ARD-CI-1: Export Definitions to CMDB

**Pre-requisites:**

1. `deployer.yml` is configured
2. `inventory.deployer` is defined
3. Generated definitions exist in:
   - `/genDefs/appDefs/*`
   - `/genDefs/regDefs/*`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started.

**Steps:**

1. The `cmdb-export` job runs in the pipeline:
   1. Reads Application Definitions from:
      - `/genDefs/appDefs/*`
   2. Reads Registry Definitions from:
      - `/genDefs/regDefs/*`
   3. Transforms definitions into CMDB-compatible payloads
   4. Pushes definitions to the configured CMDB endpoint

**Results:**

1. Application Definitions are available in CMDB
2. Registry Definitions are available in CMDB
3. CMDB contains synchronized metadata for generated definitions
4. Definitions become available for external operational consumption

