# EnvGene Configuration

- [EnvGene Configuration](#envgene-configuration)
  - [`env_definition.yml`](#env_definitionyml)
  - [`config.yml`](#configyml)
  - [`integration.yml`](#integrationyml)
  - [`deployer.yml`](#deployeryml)
  - [Artifact Definition](#artifact-definition)

## `env_definition.yml`

Environment Inventory. The inventory file of a specific Environment. Contains the "recipe" for creating an Environment. Includes:

- Reference to the Environment Template artifact
- References to environment-specific parameters:
  - Cloud passport
  - Environment-specific parameter sets
  - Environment-specific resource profiles
  - Shared credentials
- Parameters for Environment Template rendering
- Configuration parameters

Mandatory for every Environment. Created and updated manually.

Located in the Instance repository at: `/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml`  
Pass the `<cluster-name>/<env-name>` to the [`ENV_NAMES`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md#env_names) input parameter when executing Environment operations

[`env_definition.yml` JSON Schema](/schemas/env-definition.schema.json)

```yaml
# Mandatory 
inventory:
  # Mandatory
  # Name of the Environment, e.g. dev01
  # This attribute's value is available for template rendering via the `current_env.name` variable
  environmentName: string
  # Mandatory
  # Name of the Tenant for the Environment
  # This attribute's value is available for template rendering via the `current_env.tenant` variable
  tenantName: string
  # Optional
  # Name of the Cloud for the Environment
  # This attribute's value is available for template rendering via the `current_env.cloud` variable
  cloudName: string
  # Optional
  # Reference to Cloud Passport
  # Cloud Passport should be located in `/environments/<cluster-name>/<env-name>/cloud-passport/` directory
  cloudPassport: string
  # Optional
  # Reference to external CMDB system where the Environment Instance can be imported
  # Used by EnvGene extensions (not part of EnvGene Core) that implement integration with various CMDB systems
  # Should be listed in configuration/deployer.yml
  deployer: string
  # Optional 
  # Environment description
  # This attribute's value is available for template rendering via the `current_env.description` variable
  description: string
  # Optional
  # Environment owners
  # This attribute's value is available for template rendering via the `current_env.owners` variable
  owners: string
  # Optional
  config:
    # Optional. Default value - `false`
    # If `true`, during CMDB import credentials IDs will be updated using pattern:
    # <tenant-name>-<cloud-name>-<env-name>-<cred-id>
    updateCredIdsWithEnvName: boolean
    # Optional. Default value - `false`
    # If `true`, during CMDB import resource profile override names will be updated using pattern:
    # <tenant-name>-<cloud-name>-<env-name>-<RPO-name>
    updateRPOverrideNameWithEnvName: boolean
envTemplate:
  # Mandatory
  # Name of the template
  # Name should correspond to the name of template in the Environment Template artifact
  name: string
  # Mandatory
  # Template artifact in application:version notation
  artifact: string
  # Optional
  # Additional variables that will be available during template rendering
  additionalTemplateVariables: hashmap
  # Optional
  # Array of file names containing parameters that will be merged with `additionalTemplateVariables`
  # File must contain key-value hashmap
  # File must NOT located in a `parameters` directory
  sharedTemplateVariables: array
  # Optional
  # Environment specific deployment parameters set
  # The key must contain an association point - either `cloud` or name of namespace template.
  # The value must contain parameters set file name (w/o extension) located in a `parameters` directory
  envSpecificParamsets: hashmap
  # Optional
  # Environment specific pipeline (e2e) parameters set
  # The key must contain an association point - either `cloud` or name of namespace template.
  # The value must contain parameters set file name (w/o extension) located in a `parameters` directory
  envSpecificE2EParamsets: hashmap
  # Optional
  # Environment specific runtime (technical) parameters set
  # The key must contain an association point - either `cloud` or name of namespace template.
  # The value must contain parameters set file name (w/o extension) located in a `parameters` directory
  envSpecificTechnicalParamsets: hashmap
  # Optional
  # Environment specific resource profile overrides
  # The key must contain an association point - either `cloud` or name of namespace template.
  # The value must contain resource profile override file name (w/o extension) located in a `resource_profiles` directory
  envSpecificResourceProfiles: hashmap
  # Optional
  # Array of file names in a 'credentials' folder that will override generated and defined for instance credentials
  # File must contain a set of credential objects
  sharedMasterCredentialFiles: array
  # Following parameters are automatically generated during job and display that application:version artifact of template was used for last Environment generation
  generatedVersions: hashmap
```

Basic example with minimal set of fields:

```yaml
inventory:
  environmentName: "simplest-env"
  tenantName: "Applications"
envTemplate:
  name: "simple"
  artifact: "project-env-template:master_20231024-080204"
```

Full example:

```yaml
inventory:
  environmentName: "env-1"
  tenantName: "Applications"
  cloudName: "cluster-1"
  description: "Full sample"
  owners: "Qubership team"
  config:
    updateRPOverrideNameWithEnvName: false
    updateCredIdsWithEnvName: true
envTemplate:
  name: "composite-prod"
  artifact: "project-env-template:master_20231024-080204"
  additionalTemplateVariables:
    ci:
      CI_PARAM_1: ci-param-val-1
      CI_PARAM_2: ci-param-val-2
    e2eParameters:
      E2E_PARAM_1: e2e-param-val-1
      E2E_PARAM_2: e2e-param-val-2
  sharedTemplateVariables:
    - prod-template-variables
    - sample-cloud-template-variables
  envSpecificParamsets:
    bss:
      - "env-specific-bss"
      - "prod-shared"
  envSpecificTechnicalParamsets:
    bss:
      - "env-specific-tech"
  envSpecificE2EParamsets:
    cloud:
      - "cloud-level-params"
  sharedMasterCredentialFiles:
    - prod-integration-creds
```

## `config.yml`

The primary system configuration file  
Located at `/configuration/config.yml`  

[`config.yml` JSON Schema](/schemas/config.schema.json)

```yaml
# Optional. Default value - `true`
# Parameter defines the encryption mode
crypt: boolean
# Optional. Default value - `Fernet`
# Defines the encryption technology
# Requires setting an encryption key: `SECRET_KEY` or `ENVGENE_AGE_PRIVATE_KEY`, `PUBLIC_AGE_KEYS`
crypt_backend: enum [`Fernet`, `SOPS`]
# Optional. Default value - `auto`
# Defines the auto-discovery mode for Artifact Definition of env template artifact
# Used by EnvGene extensions (not part of EnvGene Core) that implement integration with various CMDB systems
# `false` - Only repository-located Artifact Definitions are used for application:version resolution
# `true` - Artifact Definition is discovered from a CMDB system (discovery procedure is not part of EnvGene Core). Discovery result is saved in repository
# `auto` - Artifact Definitions are first searched in repository, if not found - discovered from CMDB. Discovery result is saved in repository
artifact_definitions_discovery_mode: enum [`auto`, `true`, `false`]
# Optional. Default value - `true`
# Defines whether cloud passport should be decrypted upon discovery
cloud_passport_decryption: boolean
# Optional. Default value - `auto`
# Defines the auto-discovery mode for Artifact Definition of env template artifact
# Used by EnvGene extensions (not part of EnvGene Core) that implement integration with various CMDB systems
# `local` - Only repository-located Application and Registry Definitions are used for application:version resolution
# `cmdb` - Application and Registry Definitions are discovered from a CMDB system (discovery procedure is not part of EnvGene Core). Discovery result is saved in repository
# `auto` - Definitions are first searched in repository, if not found - discovered from CMDB. Discovery result is saved in repository
app_reg_def_mode: enum (`auto`, `cmdb`, `local`)
```

## `integration.yml`

System Configuration File for External Integrations

[`integration.yml` JSON Schema](/schemas/integration.schema.json)

```yaml
# Optional
# Configuration for Сloud Passport discovery integration
cp_discovery:
  # Optional
  # Parameters for GitLab-based discovery repository
  gitlab:
    # Mandatory
    # Full project path of the discovery repository
    project: string
    # Mandatory
    # Branch name of the discovery repository
    branch: master
    # Mandatory
    # Authentication token for the discovery repository
    # Recommended to set via cred macro:
    # envgen.creds.get(<cred-id>).secret
    token: string
# Authentication token for EnvGene to access the instance repository
# Required for EnvGene to commit changes to the instance repository
# Recommended to set via cred macro:
# envgen.creds.get(<cred-id>).secret
self_token: string
```

## `deployer.yml`

Contains configuration for integration with external CMDB systems. This integration enables:

- Object creation in external CMDB
- Discovery of information needed to resolve `application:version` artifact identifiers into download-ready information including:
  - Registry URL and access parameters
  - GAV coordinates (Group/Artifact/Version) of artifacts

Used by EnvGene extensions (not part of EnvGene Core) that implement integration with various CMDB systems.

Located at:

- `/configuration/deployer.yml`
- `/environments/<cluster-name>/<env-name>/app-deployer/deployer.yml`

[`deployer.yml` JSON Schema](TBD)

```yaml
# Unique name. Must be unique within a single repository
# Single file may contain multiple definitions
<name>:
  # Mandatory
  # Username for authentication with external CMDB
  # Recommended to set via cred macro:
  # envgen.creds.get(<cred-id>).secret
  username: string
  # Mandatory
  # Token for authentication with external CMDB
  # Recommended to set via cred macro:
  # envgen.creds.get(<cred-id>).secret
  token: string
  # Mandatory
  # URL of external CMDB
  deployerUrl: string
```

## Artifact Definition

The object used to resolve `application:version` identifiers of Env Templates into download-ready information including:

- Registry URL and access parameters  
- GAV coordinates (Group/Artifact/Version) of artifacts  

Each Env Template artifact requires a separate file in `/configuration/artifact_definitions/<application>.yaml`. The filename (without extension) must match the `application` from `application:version`

The Artifact Definition can be created manually or discovered via external system. The Artifact Definition discovery mechanism is controlled by `config.yaml:artifact_definitions_discovery_mode`  
The discovery is not part of EnvGene Core and can be implemented in EnvGene extensions

[Artifact Definition JSON Schema](/schemas/artifact-definition.schema.json)

```yaml
# Mandatory
# Name of the Artifact Definition (matches the `application` from `application:version`)
name: string
# Mandatory
# Group ID of the artifact
groupId: string
# Mandatory
# Artifact ID of the artifact
artifactId: string
# Mandatory
registry:
  # Mandatory
  # Registry name
  name: string
  # Mandatory
  # Credential ID for registry authentication
  # References a credential object in /configuration/credentials/credentials.yml
  credentialsId: string
  mavenConfig:
    # Mandatory
    # Registry URL
    repositoryDomainName: string
    # Mandatory
    # Snapshot repository
    # Artifacts are initially published to one repository during the build, then can be promoted to others
    # EnvGene searches for Env Template artifacts in this order: 1)Release 2)Staging 3)Snapshot
    targetSnapshot: string
    # Mandatory
    # Staging repository
    targetStaging: string
    # Mandatory
    # Release repository
    targetRelease: string
```
