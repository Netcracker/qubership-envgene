# Application and Registry Definition

- [Application and Registry Definition](#application-and-registry-definition)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
    - [Application and Registry Definitions Source](#application-and-registry-definitions-source)
      - [External Job](#external-job)
      - [User Defined by Template](#user-defined-by-template)
    - [Application and Registry Definitions Layout](#application-and-registry-definitions-layout)
      - [Template Definitions](#template-definitions)
      - [Override Definitions](#override-definitions)
      - [Rendered Definitions](#rendered-definitions)
    - [Using Application and Registry Definitions](#using-application-and-registry-definitions)
      - [Repo-level config attribute](#repo-level-config-attribute)
      - [Used by EnvGene](#used-by-envgene)
      - [Overriding Definitions](#overriding-definitions)
      - [Used by External Systems](#used-by-external-systems)
      - [Export to External CMDB Systems](#export-to-external-cmdb-systems)
    - [Application and Registry Definitions Transformation](#application-and-registry-definitions-transformation)

## Problem Statement

To work with artifacts, a short, human-readable identifier in the format `application:version` is used. This identifier should uniquely specify the artifact and where it is stored.

Using this kind of identifier means need to:

1. Make sure that each `application` in `application:version` is unique
2. Be able to resolve `application:version` into all the parameters needed to download the artifact (like registry URL, registry credentials, Maven GAV coordinates, Docker image group/name/tag, etc.)

Also need to support:

1. Identifying artifacts of different types (Maven, Docker, npm, etc.)
2. Identifying artifacts stored in different registries (Artifactory, Nexus, GCR, etc.)

## Proposed Approach

Use two types of objects:

1. [`Application Definition`](/docs/envgene-objects.md#application-definition)
  This object contains the main info about an application artifact: artifact ID, group ID, and a link to the Registry Definition.
   All environments use the centralized Application Definitions folder in the instance repository at `/genDefs/AppDefs/<application-name>.yml`.
2. [`Registry Definition`](/docs/envgene-objects.md#registry-definition)
  This object describes the registry where artifacts are stored.
   Each environment uses the centralized Registry Definitions, stored in the instance repository at `/genDefs/RegDefs/<registry-name>.yml`.

These objects are used to resolve application pointers written in the `application:version` format. They provide all the details needed to download the artifact from the correct registry.

### Application and Registry Definitions Source

There are two sources for obtaining Application and Registry Definitions in EnvGene:

#### External Job

> [!WARNING]
> The External Job-based mechanism is **deprecated**, is not recommended for use in new or actively maintained environments, and is planned to be removed in a future EnvGene release. Consumers should migrate to template-based Application and Registry Definitions as soon as reasonably possible.

An external job (not implemented in EnvGene itself, but serves as an extension point) that somehow creates/discovers/generates Application and Registry Definitions as YAML files and saves them in its artifact with the contract name `definitions.zip`.

During the [`app_reg_def_process`](/docs/envgene-pipelines.md#instance-pipeline) job execution, EnvGene retrieves the Application and Registry Definitions from this artifact and saves them in the instance repository at:

- `/appdefs`
- `/regdefs`

EnvGene uses the following instance repository pipeline parameters:

- [`APP_REG_DEFS_JOB`](/docs/instance-pipeline-parameters.md#app_reg_defs_job) - specifies which job to use
- [`APP_DEFS_PATH`](/docs/instance-pipeline-parameters.md#app_defs_path) - specifies the path within the artifact where Application Definitions are located
- [`REG_DEFS_PATH`](/docs/instance-pipeline-parameters.md#reg_defs_path) - specifies the path within the artifact where Registry Definitions are located

The External Job must be configured as part of the EnvGene Instance pipeline.

#### User Defined by Template

The user defines, in the Template repository as part of the Environment Template, templates for Application and Registry Definitions in contract path:

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

All EnvGene [`Jinja macros`](/docs/template-macros.md#jinja-macros) are available during template rendering.

Each Application and Registry Definition is created as a separate file.

During the [`app_reg_def_process`](/docs/envgene-pipelines.md#instance-pipeline) job execution, EnvGene renders these templates and generates centralized rendered definitions.

### Application and Registry Definitions Layout

EnvGene uses centralized repository-level locations for template, override, and rendered Application Definitions (AppDefs) and Registry Definitions (RegDefs).

#### Template Definitions

Jinja template definitions are stored in:

```text
/templates/appdefs/
/templates/regdefs/
```

These templates are rendered during pipeline execution using the current environment context.

#### Override Definitions

User-provided override definitions are stored in:

```text
/configuration/appdefs/
/configuration/regdefs/
```

Override definitions allow instance repositories to customize rendered definitions without modifying template source files.

#### Rendered Definitions

Final effective rendered definitions are generated in:

```text
/appdefs/
/regdefs/
```

These definitions contain the final rendered output after:

1. Jinja template rendering
2. Override processing

The rendered definitions are used during downstream deployment and CMDB integration workflows.

### Using Application and Registry Definitions

#### Repo-level config attribute

Configure the following attribute in [`config.yml`](/docs/envgene-configs.md#configyml):

```yaml
app_reg_defs_placement: dual   # default
# or
app_reg_defs_placement: root
```

##### Placement Modes

###### dual (default)

EnvGene writes rendered definitions to both:

Root-level folders:

```text
/appdefs/
/regdefs/
```

Per-environment compatibility folders:

```text
/environments/<cluster>/<env>/AppDefs/
/environments/<cluster>/<env>/RegDefs/
```

This mode is intended for backward compatibility with external consumers that still depend on the legacy per-environment folder structure.

###### root

EnvGene writes rendered definitions only to:

```text
/appdefs/
/regdefs/
```

No files are written into per-environment compatibility folders in this mode.

##### Canonical Source Behavior

Starting from the EnvGene version introducing this feature, EnvGene reads Application and Registry Definitions only from:

```text
/appdefs/
/regdefs/
```

The selected placement mode controls only where rendered files are written for compatibility purposes. Even in dual mode, the per-environment folders are treated only as compatibility mirrors for external consumers.

##### Repository-Level Configuration

The `app_reg_defs_placement` setting is configured at the repository level and applies to all environments in that repository.

This approach keeps the configuration simple, since compatibility requirements for external systems are usually the same across all environments. Managing this setting separately for each environment would add unnecessary complexity without significant benefits.

##### Deletion Behavior in dual Mode

In `dual` mode, EnvGene keeps the per-environment `AppDefs/` and `RegDefs/` folders as compatibility copies of the root-level rendered
definitions.

When definitions are removed, the mirror folders are not automatically synchronized through deletion. The behavior follows the existing root rendering approach ("last write wins").

Old definition files remain until they are manually deleted or the environment is regenerated.

##### Switching from dual to root

When migrating from dual mode to root mode, all environments should be regenerated before relying exclusively on the root-level structure.

This is important because:

Per-environment folders are generated artifacts, not authoritative sources.
Root-level definitions for a specific environment become complete only after that environment has been regenerated.
Switching to root mode before all environments are regenerated may leave outdated or stale data in the per-environment folders.
It is therefore recommended to complete regeneration for all environments before fully adopting root mode.

#### Used by EnvGene

EnvGene itself uses Application and Registry Definitions to download artifacts (like the Environment Template artifact, Solution Descriptor artifact, etc.).

These definitions are centralized across all environments. This means that for any operation on a specific environment, the system will use the definitions located at the root level.
i.e.:

```text
/appdefs/
/regdefs/
```

```text
/appdefs/
 ├── application-1.yml
 └── application-2.yml

/regdefs/
 ├── registry-1.yml
 └── registry-2.yml
```

#### Overriding Definitions

EnvGene supports overriding generated Application Definitions (AppDefs) and Registry Definitions (RegDefs) using user-provided definition files.
Generated definitions stored in:

```text
/appdefs/*
/regdefs/*
```

can be overridden by user-provided definitions located in:

```text
/configuration/appdefs/*
/configuration/regdefs/*
```

When a matching override definition exists, the user-provided definition becomes the effective definition used during downstream pipeline
processing (CMDB export & Generate Effective Set).

> [!NOTE]
The override layer is repository-wide. A single override file applies to all environments within the repository.

##### Override Matching

Override definitions are matched to generated definitions by filename.

For example:

```text
/appdefs/application-1.yml
/configuration/appdefs/application-1.yml
```

In this case, the user definition overrides the generated definition.

The YAML `name` field is not used for matching.

If filename and YAML `name` field differ, filename matching still determines the override target.

##### Override Processing Stage

Overrides are applied after Jinja template rendering is completed.

The processing flow is:

1. Template rendering
2. Generated definition creation
3. Override processing
4. Final effective definition generation

This post-render processing model allows override definitions to work with fully rendered environment-specific values.

##### Override Semantics

Override definitions use full-file replacement semantics.

If a matching override definition exists, the generated definition
is fully replaced by the override definition.

Example:

Generated definition: /appdefs/application-1.yml

```yaml
name: application-1
artifactId: application-1
groupId: org.qubership
```

Override definition: /configuration/appdefs/application-1.yml

```yaml
name: application-1
artifactId: custom-application
```

Final effective definition: /appdefs/application-1.yml

```yaml
name: application-1
artifactId: custom-application
```

In this case, groupId is removed because the override file replaces the generated definition entirely.

##### Override Definitions Without Matching Templates

If an override definition does not have a matching generated definition, the override definition is ignored.
Override processing only applies to existing generated definitions.

##### Interaction with appdefs.overrides

The existing `appdefs.overrides` Jinja-based mechanism and file-based override processing are independent features, `appdefs.overrides` applies during Jinja template rendering.

File-based overrides are applied after rendering is completed.
If both mechanisms modify the same definition, the file-based override takes precedence because it is applied later in the processing flow.

##### Migration from Per-Environment Definitions

EnvGene supports automatic migration from the legacy per-environment
AppDef and RegDef layout to the centralized definition model.

###### Legacy Layout

Previous EnvGene versions stored generated definitions inside
environment-specific directories:

- `/environments/<cluster>/<env>/AppDefs/*`
- `/environments/<cluster>/<env>/RegDefs/*`

###### Migration Behavior

During execution of the `app_reg_def_process` job:

1. Existing legacy definition files located in:
   - `/environments/<cluster>/<env>/AppDefs/*`
   - `/environments/<cluster>/<env>/RegDefs/*`

   are automatically removed.

2. Centralized definitions are regenerated from:
   - rendered templates
   - user override definitions
   
3. Override definitions are applied
   - `/configuration/appdefs/*`
   - `/configuration/regdefs/*`
   
4. Final effective definitions are written into:
   - `/appdefs/*`
   - `/regdefs/*`

###### Idempotency

The cleanup process is idempotent.

After the first successful pipeline run on an upgraded repository, subsequent executions typically find no remaining legacy files to remove.

Repeated executions therefore do not introduce additional cleanup changes.

###### Manual Migration

No manual migration steps are required for existing repositories.

Migration is handled automatically during normal pipeline execution.

#### Used by External Systems

External systems can get Application and Registry Definitions from the EnvGene instance repository using GitLab/GitHub API calls, or by checking out the repository.

Again, these definitions are shared across all environments. Therefore, for any operation on a specific environment, only the definitions located at the root level will be used:

- `/appdefs/...`
- `/regdefs/...`

#### Export to External CMDB Systems

EnvGene provides an extension point for integration with external CMDB systems, but does not implement the integration itself. As part of such integration, it is possible to create Application and Registry Definitions or their equivalents.

For this integration, the following configuration is used:

- [`CMDB_IMPORT`](/docs/instance-pipeline-parameters.md#cmdb_import): an Instance pipeline parameter that triggers the export operation
- `inventory.deployer`: an attribute in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) that points to the CMDB instance configuration
- [`deployer.yml`](/docs/envgene-configs.md#deployeryml): a configuration file that describes the parameters of the CMDB instance

### Application and Registry Definitions Transformation

When delivering a solution from one site to another, the solution artifacts are transferred from one registry to another, which affects the Application and Registry Definitions.

Usually (and best practice), the following attributes typically remain unchanged during delivery:

- group
- name
- version

However, the following attributes are usually changed:

- registry URL
- registry access parameters

To avoid recreating these definitions from scratch, it is recommended to enable transformation of the Definitions using Jinja parameterization and macros that are available exclusively for rendering Definitions:

- [`appdefs.overrides`](/docs/template-macros.md#appdefsoverrides)
- [`regdefs.overrides`](/docs/template-macros.md#regdefsoverrides)

The values for these macros are set in [`appregdef_config.yaml`](/docs/envgene-configs.md#appregdef_configyaml)

Other Jinja [`macros`](/docs/template-macros.md#jinja-macros) are also available.

For example:

- [`appregdef_config.yaml example`](/test_data/configuration/appregdef_config.yaml)
- [`Application Definition template`](/test_data/test_templates/appdefs/application-1.yaml.j2)
- [`Registry Definition template`](/test_data/test_templates/regdefs/registry-1.yaml.j2)
