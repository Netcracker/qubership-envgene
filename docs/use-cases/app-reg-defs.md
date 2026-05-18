# Application & Registry Definitions use cases

- [Application \& Registry Definitions use cases](#application--registry-definitions-use-cases)
  - [Overview](#overview)
  - [Use case groups](#use-case-groups)
  - [Template rendering](#template-rendering)
    - [UC-ARD-TR-1: Basic AppDef/RegDef template rendering](#uc-ard-tr-1-basic-appdefregdef-template-rendering)
    - [UC-ARD-TR-2: Basic AppDef/RegDef template delete](#uc-ard-tr-2-basic-appdefregdef-template-delete)
    - [UC-ARD-TR-3: Shared template repo, off-site instance rendering](#uc-ard-tr-3-shared-template-repo-off-site-instance-rendering)
    - [UC-ARD-TR-4: Shared template repo, on-site instance rendering](#uc-ard-tr-4-shared-template-repo-on-site-instance-rendering)
  - [User-provided definitions](#user-provided-definitions)
    - [UC-ARD-UD-1: Replace template-rendered definition with user-provided file](#uc-ard-ud-1-replace-template-rendered-definition-with-user-provided-file)
    - [UC-ARD-UD-2: Delete user-provided file](#uc-ard-ud-2-delete-user-provided-file)
    - [UC-ARD-UD-3: Add new definition via user-provided file with no matching template](#uc-ard-ud-3-add-new-definition-via-user-provided-file-with-no-matching-template)
  - [Placement modes](#placement-modes)
    - [UC-ARD-PM-1: Root mode behavior (auto-migration from legacy layout)](#uc-ard-pm-1-root-mode-behavior-auto-migration-from-legacy-layout)
    - [UC-ARD-PM-2: Dual mode behavior (upgrade with no cleanup)](#uc-ard-pm-2-dual-mode-behavior-upgrade-with-no-cleanup)
  - [CMDB integration](#cmdb-integration)
    - [UC-ARD-CI-1: Export definitions to CMDB](#uc-ard-ci-1-export-definitions-to-cmdb)

## Overview

This document defines use cases for Application Definitions (AppDef) and Registry Definitions (RegDef) in EnvGene.

The use cases cover:

1. Template rendering
2. Centralized definition generation
3. User-provided file processing (replace and add)
4. Placement mode behavior (root and dual, includes auto-migration from legacy layout)
5. CMDB integration
6. Definition lifecycle handling

> [!NOTE]
> Use cases below describe behavior of effective definitions written to `/appdefs/`, `/regdefs/`. In `dual` placement
> mode (default), the same effective definitions are also written as compatibility copies to
> `/environments/<cluster>/<env>/AppDefs|RegDefs/`. See the [Placement modes](#placement-modes) group for mode-specific
> upgrade scenarios.

## Use case groups

This document is organized into the following functional groups:

| Group                          | Description                                                              |
|--------------------------------|--------------------------------------------------------------------------|
| Template Rendering (TR)        | Generation of AppDef and RegDef objects from templates                   |
| User-Provided Definitions (UD) | Replace or add definitions using user-provided files                     |
| Placement Modes (PM)           | Behavior of `app_reg_def_process` in root and dual placement modes       |
| CMDB Integration (CI)          | Export and synchronization of definitions to CMDB systems                |

## Template rendering

This group covers rendering and generation of Application Definitions and Registry Definitions from templates.

### UC-ARD-TR-1: Basic AppDef/RegDef template rendering

**Pre-requisites:**

1. Template files exist in the template repository at:
   - `/templates/appdefs/app1.yml.j2`
   - `/templates/regdefs/registry1.yml.j2`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <env_name>
ENV_BUILDER: true
```

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Renders templates from:
      - `/templates/appdefs/*`
      - `/templates/regdefs/*`
   2. Writes template-rendered definitions into:
      - `/appdefs/*`
      - `/regdefs/*`

**Results:**

1. Application Definitions are generated in:
   - `/appdefs/app1.yml`
2. Registry Definitions are generated in:
   - `/regdefs/registry1.yml`

**Notes:**

- AppDef and RegDef templates can use the `appdefs.overrides` / `regdefs.overrides` Jinja macros to inject values from
  `/configuration/appregdef_config.yaml` during rendering. UC-ARD-TR-3 and UC-ARD-TR-4 cover the override-driven
  redirection scenario.
- Standard Jinja substitution makes environment variables and the current environment context available inside
  templates.
- If a template contains invalid Jinja syntax, or a rendered definition is missing required fields, the
  `app_reg_def_process` job fails with an explanatory error and the build halts.

### UC-ARD-TR-2: Basic AppDef/RegDef template delete

**Pre-requisites:**

1. Template-rendered definitions already exist in the instance repository at:
   - `/appdefs/*`
   - `/regdefs/*`

2. User removes template files from the template repository at:
   - `/templates/appdefs/*`
   - `/templates/regdefs/*`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <env_name>
ENV_BUILDER: true
```

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Renders templates from:
      - `/templates/appdefs/*`
      - `/templates/regdefs/*`
   2. Skips deletion of previously template-rendered definitions

**Results:**

1. No deletion is performed in:
   - `/appdefs/*`
   - `/regdefs/*`
2. Existing template-rendered definitions remain unchanged even when corresponding template files are deleted
3. Deletion of `/appdefs/*` and `/regdefs/*` objects is currently not supported

### UC-ARD-TR-3: Shared template repo, off-site instance rendering

**Description:**

A single template repository renders AppDef and RegDef definitions for an off-site instance repository. No registry
overrides are applied. Templates render with their default (source) registry references.

**Pre-requisites:**

1. Shared template repository:
   - AppDef templates in `/templates/appdefs/*` use the `appdefs.overrides.<key>` macro with defaults, for example:

     ```yaml
     registryName: "{{ appdefs.overrides.registryName | default('off-site-registry-X') }}"
     ```

   - RegDef templates for off-site registries exist in `/templates/regdefs/*`

2. Off-site instance repository:
   - `/configuration/appregdef_config.yaml` does not define `appdefs.overrides.registryName` (or the file is absent)

**Trigger:** Instance pipeline (GitLab or GitHub) is started in the off-site repo with `ENV_NAMES`, `ENV_BUILDER: true`.

**Steps:**

1. The `app_reg_def_process` job runs:
   1. Loads `/configuration/appregdef_config.yaml` if present
   2. Renders AppDef templates: `registryName` resolves to the template default
   3. Renders RegDef templates
   4. Writes template-rendered definitions to `/appdefs/*`, `/regdefs/*`

**Results:**

1. AppDefs in `/appdefs/*` reference off-site registries via template defaults
2. RegDefs for off-site registries are generated in `/regdefs/*`

### UC-ARD-TR-4: Shared template repo, on-site instance rendering

**Description:**

The same template repository as UC-ARD-TR-3, used in an on-site instance repository where all AppDefs are redirected to
a single on-site registry via `appregdef_config.yaml` overrides.

**Pre-requisites:**

1. Shared template repository (same as UC-ARD-TR-3): AppDef templates use the `appdefs.overrides.registryName` macro
   with off-site-registry defaults. RegDef templates include the on-site registry definition.

2. On-site instance repository:
   - `/configuration/appregdef_config.yaml`:

     ```yaml
     appdefs:
       overrides:
         registryName: on-site-registry
     ```

**Trigger:** Instance pipeline (GitLab or GitHub) is started in the on-site repo with `ENV_NAMES`, `ENV_BUILDER: true`.

**Steps:**

1. The `app_reg_def_process` job runs:
   1. Loads `/configuration/appregdef_config.yaml` and exposes `appdefs.overrides` to the Jinja context
   2. Renders AppDef templates: `registryName` resolves to `on-site-registry` (override beats default)
   3. Renders RegDef templates
   4. Writes template-rendered definitions to `/appdefs/*`, `/regdefs/*`

**Results:**

1. All AppDefs in `/appdefs/*` reference `on-site-registry`
2. The on-site RegDef is generated in `/regdefs/*` and referenced by all AppDefs
3. RegDefs for off-site registries are still generated and remain in `/regdefs/*` (unused after redirection)

## User-provided definitions

This group covers customizing template-rendered definitions via user-provided files placed in `/configuration/appdefs/`,
`/configuration/regdefs/`. A user-provided file can either replace an existing template-rendered definition or add a new
definition that has no template counterpart.

### UC-ARD-UD-1: Replace template-rendered definition with user-provided file

**Pre-requisites:**

1. Template-rendered definitions exist in the instance repository at:
   - `/appdefs/*`
   - `/regdefs/*`

2. User-provided files with filenames matching existing template-rendered definitions exist in the instance repository
   at:
   - `/configuration/appdefs/*`
   - `/configuration/regdefs/*`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <env_name>
ENV_BUILDER: true
```

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Renders templates from:
      - `/templates/appdefs/*`
      - `/templates/regdefs/*`
   2. Writes template-rendered definitions into:
      - `/appdefs/*`
      - `/regdefs/*`
   3. Discovers user-provided files in:
      - `/configuration/appdefs/*`
      - `/configuration/regdefs/*`
   4. Replaces template-rendered definitions with user-provided files (filename-matched)

**Results:**

1. User-provided files from:
   - `/configuration/appdefs/*`
   - `/configuration/regdefs/*`
   replace template-rendered definitions in:
   - `/appdefs/*`
   - `/regdefs/*`
2. User-provided files take precedence during downstream processing
3. Final effective definitions contain user-provided file content

### UC-ARD-UD-2: Delete user-provided file

**Pre-requisites:**

1. Template-rendered definitions exist in the instance repository at:
   - `/appdefs/*`
   - `/regdefs/*`

2. User-provided files previously existed in the instance repository at:
   - `/configuration/appdefs/*`
   - `/configuration/regdefs/*`

3. User deletes the files from the instance repository at:
   - `/configuration/appdefs/*`
   - `/configuration/regdefs/*`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started with parameters:

```yaml
ENV_NAMES: <env_name>
ENV_BUILDER: true
```

**Steps:**

1. The `app_reg_def_process` job runs in the pipeline:
   1. Renders templates from:
      - `/templates/appdefs/*`
      - `/templates/regdefs/*`
   2. Writes template-rendered definitions into:
      - `/appdefs/*`
      - `/regdefs/*`
   3. Detects deleted user-provided files
   4. Skips user-provided file processing for deleted files
   5. Retains template-rendered definitions as effective definitions

**Results:**

1. No deletion is performed in:
   - `/appdefs/*`
   - `/regdefs/*`
2. Existing template-rendered definitions remain active when user-provided files are deleted
3. Effective definitions revert back to template-rendered definitions for entries where the user-provided file was
   replacing a template-rendered one
4. Deleting a user-provided file only removes its replacement behavior and does not delete template-rendered definitions

### UC-ARD-UD-3: Add new definition via user-provided file with no matching template

**Description:**

A user-provided file is placed in `/configuration/appdefs/*` or `/configuration/regdefs/*` and has no corresponding
template-rendered definition at the same filename. The user-provided file becomes a new effective definition alongside
template-rendered ones.

**Pre-requisites:**

1. Template-rendered definitions exist in the instance repository at `/appdefs/*`, `/regdefs/*`.
2. A user-provided file is placed in the instance repository at `/configuration/appdefs/new-app.yml` (or
   `/configuration/regdefs/new-registry.yml`) where the filename does not match any rendered template output.

**Trigger:** Instance pipeline (GitLab or GitHub) is started with `ENV_NAMES`, `ENV_BUILDER: true`.

**Steps:**

1. The `app_reg_def_process` job runs:
   1. Renders templates from `/templates/appdefs/*`, `/templates/regdefs/*`
   2. Writes template-rendered definitions into `/appdefs/*`, `/regdefs/*`
   3. Discovers user-provided files in `/configuration/appdefs/*`, `/configuration/regdefs/*`
   4. For each user-provided file, looks up the matching template-rendered definition by filename
   5. For files with no matching template, adds them as new effective definitions at `/appdefs/<filename>` (or
      `/regdefs/<filename>`)

**Results:**

1. User-provided file `/configuration/appdefs/new-app.yml` becomes a new effective definition at `/appdefs/new-app.yml`
2. Existing template-rendered definitions remain unchanged

## Placement modes

This group covers behavior of the `app_reg_def_process` job in each placement mode (`root` and `dual`). Both UCs use
the upgrade-from-legacy-layout scenario as the canonical illustration. The same Steps apply in steady state when no
legacy files exist (`root` cleanup finds nothing to remove, and `dual` writes copies without legacy coexistence).

### UC-ARD-PM-1: Root mode behavior (auto-migration from legacy layout)

**Description:**

On an upgraded instance repository configured for `root` placement mode, the `app_reg_def_process` job removes legacy
per-environment AppDef/RegDef files and writes effective definitions only at the root level.

**Pre-requisites:**

1. Legacy per-environment files exist in the instance repository at:
   - `/environments/<cluster>/<env>/AppDefs/*`
   - `/environments/<cluster>/<env>/RegDefs/*`

2. Instance repository is upgraded to the EnvGene version that uses the centralized layout (`/appdefs/*`, `/regdefs/*`).

3. Instance repository is configured for `root` placement mode:

   ```yaml
   app_reg_defs_placement: root
   ```

4. Template repository contains AppDef and RegDef templates in `/templates/appdefs/*`, `/templates/regdefs/*`.

**Trigger:** Instance pipeline (GitLab or GitHub) is started with `ENV_NAMES`, `ENV_BUILDER: true`.

**Steps:**

1. The `app_reg_def_process` job runs:
   1. Renders AppDef and RegDef templates with current environment context
   2. Applies user-provided files from `/configuration/appdefs/*`, `/configuration/regdefs/*` (if present)
   3. Writes final effective definitions into `/appdefs/*`, `/regdefs/*`
   4. Removes any files in:
      - `/environments/<cluster>/<env>/AppDefs/*`
      - `/environments/<cluster>/<env>/RegDefs/*`

**Results:**

1. Legacy per-environment AppDef and RegDef files are removed from the repository
2. Centralized definitions exist in `/appdefs/*`, `/regdefs/*`
3. Subsequent pipeline runs find no remaining legacy files to remove (idempotent cleanup)
4. No manual migration steps are required

### UC-ARD-PM-2: Dual mode behavior (upgrade with no cleanup)

**Description:**

On an upgraded instance repository configured for `dual` placement mode (default), no migration cleanup is performed.
Legacy per-environment files coexist with new dual-mode compatibility copies.

**Pre-requisites:**

1. Legacy per-environment files exist in the instance repository at:
   - `/environments/<cluster>/<env>/AppDefs/*`
   - `/environments/<cluster>/<env>/RegDefs/*`

2. Instance repository is upgraded to the EnvGene version that uses the centralized layout (`/appdefs/*`, `/regdefs/*`).

3. Instance repository is configured for `dual` placement mode:

   ```yaml
   app_reg_defs_placement: dual
   ```

4. Template repository contains AppDef and RegDef templates in `/templates/appdefs/*`, `/templates/regdefs/*`.

**Trigger:** Instance pipeline (GitLab or GitHub) is started with `ENV_NAMES`, `ENV_BUILDER: true`.

**Steps:**

1. The `app_reg_def_process` job runs:
   1. Renders AppDef and RegDef templates with current environment context
   2. Applies user-provided files from `/configuration/appdefs/*`, `/configuration/regdefs/*` (if present)
   3. Writes effective definitions to `/appdefs/*`, `/regdefs/*`
   4. Writes per-environment compatibility copies to `/environments/<cluster>/<env>/AppDefs/*`,
      `/environments/<cluster>/<env>/RegDefs/*`, overwriting any pre-existing files with matching names
   5. Does not touch per-environment files whose names do not match any current template-rendered or user-provided
      definition

**Results:**

1. Files in `/appdefs/*`, `/regdefs/*` contain current effective definitions
2. Per-environment folders contain copies of the current files
3. Legacy files with names matching current definitions are overwritten with fresh content
4. Legacy files with names not matching anything (orphans) persist until manually removed or the environment is
   regenerated

## CMDB integration

This group covers integration and synchronization of Application Definitions and Registry Definitions with external CMDB
systems.

### UC-ARD-CI-1: Export definitions to CMDB

**Pre-requisites:**

1. `deployer.yml` is configured
2. `inventory.deployer` is defined
3. Template-rendered definitions exist in the instance repository at:
   - `/appdefs/*`
   - `/regdefs/*`

**Trigger:**

Instance pipeline (GitLab or GitHub) is started.

**Steps:**

1. During pipeline execution, the `app_reg_def_process` job renders
template-rendered AppDefs and RegDefs from templates.
If matching user-provided files exist in:
   - `/configuration/appdefs/*`
   - `/configuration/regdefs/*`
the user-provided files fully replace the corresponding template-rendered
definitions in:
   - `/appdefs/*`
   - `/regdefs/*`

2. The `cmdb_import` job runs in the pipeline:
   2.1. Reads Application Definitions from:
      - `/appdefs/*`
   2.2. Reads Registry Definitions from:
      - `/regdefs/*`
   2.3. Transforms definitions into CMDB-compatible payloads
   2.4. Pushes definitions to the configured CMDB endpoint

**Results:**

1. Application Definitions are available in CMDB
2. Registry Definitions are available in CMDB
3. CMDB contains synchronized metadata for effective definitions

As a result, CMDB always receives the effective runtime definitions
used by downstream deployment processes.
