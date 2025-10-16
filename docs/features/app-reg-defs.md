# Application and Registry Definition

- [Application and Registry Definition](#application-and-registry-definition)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
    - [Application and Registry Definitions Source](#application-and-registry-definitions-source)
      - [External Job](#external-job)
      - [User Defined by Template](#user-defined-by-template)
    - [Using Application and Registry Definitions](#using-application-and-registry-definitions)
      - [Used by EnvGene](#used-by-envgene)
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

1. [Application Definition](/docs/envgene-objects.md#application-definition)
   This object contains the main info about an application artifact: artifact ID, group ID, and a link to the Registry Definition.
   Each Environment has its own set of Application Definitions, stored in the Instance repository at `/environments/<cluster-name>/<env-name>/AppDefs/<application-name>.yml`.

2. [Registry Definition](/docs/envgene-objects.md#registry-definition)
   This object describes the registry where artifacts are stored.
   Each Environment has its own set of Registry Definitions, stored in the Instance repository at `/environments/<cluster-name>/<env-name>/AppDefs/<registry-name>.yml`.

These objects are used to resolve application pointers written in the `application:version` format. They provide all the details needed to download the artifact from the correct registry.

### Application and Registry Definitions Source

There are two sources for obtaining Application and Registry Definitions in EnvGene:

#### External Job

An external job (not implemented in EnvGene itself, but serves as an extension point) that somehow creates/discovers/generates Application and Registry Definitions as YAML files and saves them in its artifact with the contract name `definitions.zip`.

During the generation of an Environment Instance (as part of `env_build_job`), EnvGene retrieves the Application and Registry Definitions from this artifact and saves them as part of the environment instance.

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

These files can be either Jinja templates of the object or plain objects without parameterization. All EnvGene [Jinja macros](/docs/template-macros.md#jinja-macros) are available for template creation.

Each Application and Registry Definition is created as a separate file.

During Environment Instance generation (as part of `env_build_job`), EnvGene renders these templates and saves them as part of the Environment Instance.

### Using Application and Registry Definitions

#### Used by EnvGene

EnvGene itself uses Application and Registry Definitions to download artifacts (like the Environment Template artifact, Solution Descriptor artifact, etc.).

These definitions are environment-specific. This means that for any operation on a particular Environment, only the definitions located in that environment are used, i.e.:

- `/environments/<cluster-name>/<env-name>/AppDefs/...`
- `/environments/<cluster-name>/<env-name>/RegDefs/...`

```text
/environments/
└── <cluster-name>/
    └── <env-name>/
        ├── AppDefs/                   # Application Definitions
        │   ├── application-1.yml
        │   └── application-2.yml
        └── RegDefs/                   # Registry Definitions
            ├── registry-1.yml
            └── registry-2.yml
```

#### Used by External Systems

External systems can get Application and Registry Definitions from the EnvGene instance repository using GitLab/GitHub API calls, or by checking out the repository.

Again, these definitions are environment-specific. So, for any operation on a specific environment, only the definitions from that environment should be used:

- `/environments/<cluster-name>/<env-name>/AppDefs/...`
- `/environments/<cluster-name>/<env-name>/RegDefs/...`

#### Export to External CMDB Systems

EnvGene provides an extension point for integration with external CMDB systems, but does not implement the integration itself. As part of such integration, it is possible to create Application and Registry Definitions or their equivalents.

For this integration, the following configuration is used:

- [`CMDB_IMPORT`](/docs/instance-pipeline-parameters.md#cmdb_import): a Instance pipeline parameter that triggers the export operation
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

Other Jinja [macros](/docs/template-macros.md#jinja-macros) are also available.

For example:

- [appregdef_config.yaml example](/test_data/configuration/appregdef_config.yaml)
- [Application Definition template](/test_data/test_templates/appdefs/application-1.yaml.j2)
- [Registry Definition template](/test_data/test_templates/regdefs/registry-1.yaml.j2)
