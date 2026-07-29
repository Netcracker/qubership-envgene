# Application and Registry Definition

- [Application and Registry Definition](#application-and-registry-definition)
  - [Overview](#overview)
  - [Definition sources](#definition-sources)
    - [Templates](#templates)
    - [Definition overrides](#definition-overrides)
    - [External Job (deprecated)](#external-job-deprecated)
  - [Processing](#processing)
  - [Output layout](#output-layout)
    - [Placement modes](#placement-modes)
  - [Consumers](#consumers)
    - [EnvGene](#envgene)
    - [External systems](#external-systems)
    - [Import into external CMDB systems](#import-into-external-cmdb-systems)
  - [Template transformation](#template-transformation)
  - [See also](#see-also)

## Overview

Using Application and Registry Definition, EnvGene resolves an `application:version` pointer into the parameters
needed to download the artifact:

1. [Application Definition](/docs/envgene-objects.md#application-definition) (AppDef) - describes an application
   artifact and references a Registry Definition.
2. [Registry Definition](/docs/envgene-objects.md#registry-definition) (RegDef) - describes a registry and its access
   parameters.

An AppDef, and a RegDef for its registry, must exist for every Solution Descriptor (SD) used in the repository and
for every application the SDs reference.

Effective definitions live in the root-level folders of the instance repository:

```text
/appdefs/<name>.yml
/regdefs/<name>.yml
```

Depending on the [placement mode](#placement-modes), EnvGene also maintains the per-environment folders
`/environments/<cluster>/<env>/AppDefs/` and `/environments/<cluster>/<env>/RegDefs/`, which hold the
definitions of the current build rather than a copy of the root-level content.

EnvGene assembles effective definitions from two sources:

- **Templates** - Jinja or plain YAML files in the template repository, rendered with the current environment context.
- **Definition overrides** - plain YAML files in the instance repository that replace template-rendered definitions or
  add new ones.

A deprecated [External Job](#external-job-deprecated) path can supply definitions instead of these sources.

## Definition sources

### Templates

Templates are stored in the template repository:

```text
/templates/
 ├── appdefs/                        # Application Definition templates
 │   ├── app1.yml.j2
 │   └── app2.yml.j2
 └── regdefs/                        # Registry Definition templates
     ├── registry1.yml.j2
     └── registry2.yml.j2
```

EnvGene processes files matching `*.yaml.j2`, `*.yml.j2`, `*.j2`, `*.yaml`, or `*.yml`. A template is either a Jinja
template or a plain YAML definition without parameterization. All EnvGene
[Jinja macros](/docs/template-macros.md#jinja-macros) are available during rendering. Each definition is a separate
file.

Templates are rendered during the [`app_reg_def_process`](/docs/envgene-pipelines.md#instance-pipeline) pipeline stage.
In GitLab pipelines the stage runs as the `app_reg_def_render.<cluster>/<env>` job. In GitHub Actions it runs as the
`APP_REG_DEF_PROCESS` step.

A template-rendered definition is written as `<name>.yml`, where `<name>` is the value of the `name` field of the
rendered YAML, not the template filename. Template-rendered definitions are schema-validated after rendering, and
the stage fails on a violation.

### Definition overrides

Definition overrides are stored in the instance repository:

```text
/configuration/
 ├── appdefs/
 └── regdefs/
```

EnvGene processes files with the `.yml` or `.yaml` extension. Nested directories are not scanned. Definition
overrides are plain YAML and are used as-is. They are never rendered as Jinja: they apply after template rendering
completes, so no Jinja context is available.

Each definition override is copied over the output of template rendering:

- A file with the same filename as a template-rendered definition fully replaces it. There is no field-level merge:
  fields omitted from the definition override are lost.
- A file with no counterpart is added as a new effective definition.

Because template-rendered definitions are named by their `name` field, a definition override that replaces one must
match that name, not the template filename.

Definition overrides apply repository-wide: the same files are applied on every environment build. They are not
schema-validated, because validation runs on the render output before definition overrides are applied.

The [`appdefs.overrides` and `regdefs.overrides`](#template-transformation) macros apply during template rendering. A
definition override applies later and replaces the whole definition, including any values the macros produced.

### External Job (deprecated)

> [!WARNING]
> The External Job mechanism is **deprecated** and is planned to be removed in a future EnvGene release. Migrate to
> template-based Application and Registry Definitions as soon as reasonably possible.

An External Job is an extension point: a job, not implemented by EnvGene, produces AppDef and RegDef YAML files in its
job artifact. The following Instance pipeline parameters configure it:

- [`APP_REG_DEFS_JOB`](/docs/instance-pipeline-parameters.md#app_reg_defs_job) - specifies the job that produces the
  artifact
- [`APP_DEFS_PATH`](/docs/instance-pipeline-parameters.md#app_defs_path) - specifies the path within the artifact where
  Application Definitions are located
- [`REG_DEFS_PATH`](/docs/instance-pipeline-parameters.md#reg_defs_path) - specifies the path within the artifact where
  Registry Definitions are located

The pipeline copies the files from the artifact into the per-environment folders before Solution Descriptor processing
and Effective Set generation. GitLab pipelines additionally copy them into the root-level folders.

The External Job path is not handled by the `app_reg_def_process` stage. It should not be combined with the template
and definition override flow in the same repository.

## Processing

For each environment, the `app_reg_def_process` stage:

1. Renders templates and validates the result (see [Templates](#templates)).
2. Merges the render output into the root-level folders. Files with the same name are overwritten. Other files are
   kept.
3. Deletes the per-environment folders. In [`dual` placement mode](#placement-modes), recreates them as an exact copy
   of the render output.
4. Copies definition overrides into the root-level folders, and in `dual` mode also into the per-environment folders.

## Output layout

The root-level folders hold the effective definitions and are committed to the instance repository. Because they are
merged into and never cleaned (see [Processing](#processing)), a definition whose template was removed persists at the
root level until deleted manually. This applies in both placement modes.

In `dual` mode the per-environment folders always mirror the current render output plus definition overrides, so
deletions are propagated there.

### Placement modes

The `app_reg_defs_placement` attribute in [`config.yml`](/docs/envgene-configs.md#configyml) selects the placement
mode. It is set at the repository level and applies to all environments.

- **`dual` (default)** - root-level folders plus per-environment compatibility copies. The mode exists for backward
  compatibility only and is planned to be removed in a future EnvGene release together with the per-environment
  folders. Migrate consumers to the root-level folders and switch to `root`.
- **`root`** - root-level folders only. No per-environment copies are maintained.

## Consumers

### EnvGene

EnvGene resolves `application:version` references through the definitions in two operations:

- SD download.
- [Effective Set generation](/docs/features/effective-set-generation.md), which resolves every application referenced
  by the SDs it processes.

For how EnvGene searches the registries and resolves the version to download an artifact, see
[Artifact Resolution](/docs/features/artifact-resolution.md).

Resolution reads the root-level folders first and falls back to the per-environment folders. The fallback exists for
backward compatibility only: all consumers must migrate to the root-level folders.

> [!NOTE]
> The Environment Template artifact is also downloaded by `application:version`, but its resolution uses an
> [Artifact Definition](/docs/envgene-objects.md#artifact-definition) stored at
> `/configuration/artifact_definitions/`, not an AppDef. AppDefs are delivered by the Environment Template artifact
> itself, so they cannot drive its own download. An Artifact Definition is authored manually for each such artifact
> used in the repository.

### External systems

External systems read the root-level folders from the instance repository, via Git API or repository checkout. Legacy
consumers that depend on the per-environment layout are served by `dual` mode.

### Import into external CMDB systems

CMDB import is an extension point. EnvGene does not implement the integration itself. The configuration contract:

- [`CMDB_IMPORT`](/docs/instance-pipeline-parameters.md#cmdb_import) - an Instance pipeline parameter that triggers
  the import operation
- `inventory.deployer` - an attribute in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) that
  points to the CMDB instance configuration
- [`deployer.yml`](/docs/envgene-configs.md#deployeryml) - a configuration file that describes the parameters of the
  CMDB instance

## Template transformation

Site-to-site delivery transfers solution artifacts from one registry to another. The artifact group, name, and version
stay the same, while the registry URL and registry access parameters change. Instead of recreating the definitions for
each site, parameterize the templates with macros available exclusively when rendering definitions:

- [`appdefs.overrides`](/docs/template-macros.md#appdefsoverrides)
- [`regdefs.overrides`](/docs/template-macros.md#regdefsoverrides)

The values for these macros come from [`appregdef_config.yaml`](/docs/envgene-configs.md#appregdef_configyaml).

For example:

- [`appregdef_config.yaml` example](/test_data/test_app_reg_defs/TC-001-003/environments/configuration/appregdef_config.yaml)
- [Application Definition template](/test_data/test_templates/appdefs/application-1.yaml.j2)
- [Registry Definition template](/test_data/test_templates/regdefs/registry-1.yaml.j2)

## See also

- [Add Application or Registry Definitions to the template repository](/docs/how-to/app-reg-defs-add-to-template.md) -
  how-to for authoring definition templates.
- [Add an Application or Registry Definition without a template](/docs/how-to/app-reg-defs-add-without-template.md) -
  how-to for adding a definition override in the instance repository.
- [Application and Registry Definitions use cases](/docs/use-cases/app-reg-defs.md) - rendering, override, and
  placement-mode scenarios.
- [Artifact downloading use cases](/docs/use-cases/artifact-downloading.md) - supported registries and authentication
  for SD and Environment Template downloads.
