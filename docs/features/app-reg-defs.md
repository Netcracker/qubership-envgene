# Application and Registry Definition

- [Application and Registry Definition](#application-and-registry-definition)
  - [Problem statement](#problem-statement)
  - [Proposed approach](#proposed-approach)
  - [Definition sources](#definition-sources)
    - [Templates](#templates)
    - [User-provided files](#user-provided-files)
      - [Filename matching](#filename-matching)
      - [Replacement semantics](#replacement-semantics)
      - [Interaction with appdefs.overrides macro](#interaction-with-appdefsoverrides-macro)
    - [External Job (deprecated)](#external-job-deprecated)
  - [Processing order](#processing-order)
  - [Output layout](#output-layout)
    - [Rendered output](#rendered-output)
    - [Placement modes](#placement-modes)
  - [Migration from per-environment layout](#migration-from-per-environment-layout)
  - [Consumers](#consumers)
    - [EnvGene](#envgene)
    - [External systems](#external-systems)
    - [Export to external CMDB systems](#export-to-external-cmdb-systems)
  - [Template transformation](#template-transformation)

## Problem statement

To work with artifacts, a short, human-readable identifier in the format `application:version` is used. This identifier
should uniquely specify the artifact and where it is stored.

Using this kind of identifier means need to:

1. Make sure that each `application` in `application:version` is unique
2. Be able to resolve `application:version` into all the parameters needed to download the artifact (like registry URL,
   registry credentials, Maven GAV coordinates, Docker image group/name/tag, etc.)

Also need to support:

1. Identifying artifacts of different types (Maven, Docker, npm, etc.)
2. Identifying artifacts stored in different registries (Artifactory, Nexus, GCR, etc.)

## Proposed approach

EnvGene uses two types of objects to resolve `application:version` pointers into all the parameters needed to download
an artifact:

1. [Application Definition](/docs/envgene-objects.md#application-definition) (AppDef) - describes an application
   artifact (artifact ID, group ID) and references a Registry Definition. Lives in `/appdefs/<application-name>.yml`.
2. [Registry Definition](/docs/envgene-objects.md#registry-definition) (RegDef) - describes a registry (URL,
   credentials, type). Lives in `/regdefs/<registry-name>.yml`.

EnvGene assembles effective definitions from three sources:

- **Templates** - Jinja or plain YAML files in the template repository, rendered with the current environment context.
- **User-provided files** (YAML in `/configuration/appdefs/`, `/configuration/regdefs/`) - replace template-rendered
  definitions or add new ones, matched by filename.
- **External Job** (deprecated) - files extracted from a job artifact.

Effective definitions are written to `/appdefs/` and `/regdefs/` at the repository root, where EnvGene itself and
external systems read them.

## Definition sources

EnvGene assembles Application and Registry Definitions from three sources, described below. When two sources produce a
file with the same name, **user-provided files win over template-rendered definitions**. The External Job is a
deprecated alternative path that should not be combined with the template + user-provided file flow in the same
repository.

### Templates

Templates are stored in the template repository at:

- `/templates/appdefs/<application-name>.yaml|yml|yml.j2|yaml.j2`
- `/templates/regdefs/<registry-name>.yaml|yml|yml.j2|yaml.j2`

```text
/templates/
 ├── appdefs/                        # Application Definitions templates
 │   ├── app1.yml.j2
 │   └── app2.yml.j2
 └── regdefs/                        # Registry Definitions templates
     ├── registry1.yml.j2
     └── registry2.yml.j2
```

These files can be either:

- Jinja templates
- plain YAML definitions without parameterization

All EnvGene [Jinja macros](/docs/template-macros.md#jinja-macros) are available during template rendering.

Each Application and Registry Definition is created as a separate file.

During the [`app_reg_def_process`](/docs/envgene-pipelines.md#instance-pipeline) job execution, EnvGene renders these
templates and generates rendered definitions.

### User-provided files

User-provided files are stored in the instance repository at:

- `/configuration/appdefs/<application-name>.yaml|yml`
- `/configuration/regdefs/<registry-name>.yaml|yml`

User-provided files are plain YAML and used as-is. They are **not** rendered as Jinja templates: file-based processing
applies after Jinja template rendering is completed (see [Processing order](#processing-order)), so no Jinja context is
available.

Each user-provided file is matched by filename against the template-rendered definitions:

- **Match exists** - the user-provided file fully replaces the template-rendered definition. The user-provided file
  becomes the effective definition.
- **No match** - the user-provided file is added as a new effective definition with no template counterpart.

In both cases, the resulting effective definition is used during downstream pipeline processing (CMDB export & Generate
Effective Set).

> [!NOTE]
> User-provided files apply repository-wide, not per-environment. The same file affects all environments in the
> repository.

#### Filename matching

Files are matched by filename only. The YAML `name` field is not used for matching.

For example:

```text
/appdefs/application-1.yml
/configuration/appdefs/application-1.yml
```

In this case, the user-provided file replaces the template-rendered definition.

If the filename and YAML `name` field differ, filename matching still determines the target.

#### Replacement semantics

User-provided files use full-file replacement: every field that should remain in the final definition must be present in
the user-provided file. Fields omitted from the user-provided file are lost - there is no field-level merge.

#### Interaction with appdefs.overrides macro

The `appdefs.overrides` Jinja-based mechanism and file-based user-provided processing are independent features.
`appdefs.overrides` applies during Jinja template rendering.

File-based processing applies after rendering is completed. If both mechanisms modify the same definition, the
file-based user-provided file takes precedence because it is applied later in the processing flow.

See [Template transformation](#template-transformation) for the typical use case of the `appdefs.overrides` and
`regdefs.overrides` macros.

### External Job (deprecated)

> [!WARNING]
> The External Job-based mechanism is **deprecated**, is not recommended for use in new or actively maintained
> environments, and is planned to be removed in a future EnvGene release. Consumers should migrate to template-based
> Application and Registry Definitions as soon as reasonably possible.

An external job (not implemented in EnvGene itself, but serves as an extension point) that somehow
creates/discovers/generates Application and Registry Definitions as YAML files and saves them in its artifact with the
contract name `definitions.zip`.

During the [`app_reg_def_process`](/docs/envgene-pipelines.md#instance-pipeline) job execution, EnvGene retrieves the
Application and Registry Definitions from this artifact and saves them in the instance repository at:

- `/appdefs/`
- `/regdefs/`

EnvGene uses the following instance repository pipeline parameters:

- [`APP_REG_DEFS_JOB`](/docs/instance-pipeline-parameters.md#app_reg_defs_job) - specifies which job to use
- [`APP_DEFS_PATH`](/docs/instance-pipeline-parameters.md#app_defs_path) - specifies the path within the artifact where
  Application Definitions are located
- [`REG_DEFS_PATH`](/docs/instance-pipeline-parameters.md#reg_defs_path) - specifies the path within the artifact where
  Registry Definitions are located

The External Job must be configured as part of the EnvGene Instance pipeline.

## Processing order

The `app_reg_def_process` job assembles effective definitions:

1. Render templates from `/templates/appdefs/`, `/templates/regdefs/` using the current environment context, producing
   definitions in `/appdefs/`, `/regdefs/`.
2. Apply user-provided files from `/configuration/appdefs/`, `/configuration/regdefs/`:
   - For each user-provided file with a matching template-rendered definition (by filename), replace the
     template-rendered definition.
   - For each user-provided file with no matching template-rendered definition, add it as a new effective definition.
3. Apply [placement mode](#placement-modes):
   - In `dual` mode: write per-environment compatibility copies of effective definitions to
     `/environments/<cluster>/<env>/AppDefs|RegDefs/*`.
   - In `root` mode: remove any pre-existing files from `/environments/<cluster>/<env>/AppDefs|RegDefs/*`.

This post-render processing model allows user-provided files to operate on fully rendered environment-specific values
and avoids requiring Jinja-aware user-provided files.

If the [External Job (deprecated)](#external-job-deprecated) is configured, files extracted from its artifact are
written directly to `/appdefs/`, `/regdefs/`. The External Job is a deprecated alternative path and should not be
combined with the template + user-provided file flow in the same repository.

## Output layout

### Rendered output

Final effective rendered definitions are generated in:

```text
/appdefs/
/regdefs/
```

These definitions contain the final rendered output after:

1. Jinja template rendering
2. User-provided file processing

The rendered definitions are used during downstream deployment and CMDB integration workflows.

### Placement modes

EnvGene can write rendered definitions to per-environment compatibility folders alongside the root-level locations, for
backward compatibility with external consumers that still depend on the legacy per-environment folder structure. This is
controlled by the `app_reg_defs_placement` attribute in [`config.yml`](/docs/envgene-configs.md#configyml):

```yaml
app_reg_defs_placement: dual   # default
# or
app_reg_defs_placement: root
```

- **`dual` (default)** - writes to root-level folders (`/appdefs/`, `/regdefs/`) AND to per-environment compatibility
  folders (`/environments/<cluster>/<env>/AppDefs|RegDefs/`). Deletions are not synced to per-environment folders - old
  copies persist until manually deleted or the environment is regenerated (last-write-wins).
- **`root`** - writes only to root-level folders. No files are written into per-environment compatibility folders.
  Existing per-environment files are removed by `app_reg_def_process` on each run (see
  [Migration](#migration-from-per-environment-layout)). When switching from `dual` to `root`, regenerate all
  environments first to ensure root-level definitions are complete.

The setting is configured at the repository level and applies to all environments. Per-environment granularity would add
complexity without benefits, since compatibility requirements are typically the same across all environments.

> [!NOTE]
> Placement modes only control **where rendered files are written**. EnvGene itself always reads Application and
> Registry Definitions from `/appdefs/` and `/regdefs/` regardless of the selected mode. In `dual` mode, the
> per-environment folders are compatibility copies for external consumers - EnvGene does not read from them.

## Migration from per-environment layout

Earlier EnvGene versions stored generated AppDefs and RegDefs in per-environment directories
(`/environments/<cluster>/<env>/AppDefs|RegDefs/*`). These directories are handled depending on the configured
[placement mode](#placement-modes):

- **`root` mode** - the `app_reg_def_process` job removes any files found in these directories on each run. The cleanup
  is idempotent and requires no manual migration steps.
- **`dual` mode** - no migration cleanup is performed. The per-environment folders are actively used as compatibility
  copies managed by the [placement mode](#placement-modes) itself.

## Consumers

### EnvGene

EnvGene itself uses Application and Registry Definitions to download artifacts (Environment Template, Solution
Descriptor, etc.) from `/appdefs/` and `/regdefs/`.

### External systems

External systems can read Application and Registry Definitions directly from `/appdefs/` and `/regdefs/` in the instance
repository (via Git API or repository checkout).

For external consumers that still depend on the legacy per-environment folder structure, EnvGene can also write
compatibility copies to `/environments/<cluster>/<env>/AppDefs|RegDefs/` via the `dual` [placement
mode](#placement-modes).

### Export to external CMDB systems

EnvGene provides an extension point for integration with external CMDB systems, but does not implement the integration
itself. As part of such integration, it is possible to create Application and Registry Definitions or their equivalents.

The `cmdb_import` job reads Application and Registry Definitions from `/appdefs/` and `/regdefs/` (the root-level
locations, regardless of placement mode) and pushes them to the configured CMDB endpoint.

For this integration, the following configuration is used:

- [`CMDB_IMPORT`](/docs/instance-pipeline-parameters.md#cmdb_import): an Instance pipeline parameter that triggers the
  export operation
- `inventory.deployer`: an attribute in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) that
  points to the CMDB instance configuration
- [`deployer.yml`](/docs/envgene-configs.md#deployeryml): a configuration file that describes the parameters of the CMDB
  instance

## Template transformation

When delivering a solution from one site to another, the solution artifacts are transferred from one registry to
another, which affects the Application and Registry Definitions.

Usually (and best practice), the following attributes typically remain unchanged during delivery:

- group
- name
- version

However, the following attributes are usually changed:

- registry URL
- registry access parameters

To avoid recreating these definitions from scratch, it is recommended to enable transformation of the Definitions using
Jinja parameterization and macros that are available exclusively for rendering Definitions:

- [`appdefs.overrides`](/docs/template-macros.md#appdefsoverrides)
- [`regdefs.overrides`](/docs/template-macros.md#regdefsoverrides)

The values for these macros are set in [`appregdef_config.yaml`](/docs/envgene-configs.md#appregdef_configyaml).

Other Jinja [macros](/docs/template-macros.md#jinja-macros) are also available.

For example:

- [`appregdef_config.yaml` example](/test_data/configuration/appregdef_config.yaml)
- [Application Definition template](/test_data/test_templates/appdefs/application-1.yaml.j2)
- [Registry Definition template](/test_data/test_templates/regdefs/registry-1.yaml.j2)
