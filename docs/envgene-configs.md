# EnvGene Objects

- [EnvGene Objects](#envgene-objects)
  - [`env_definition.yml`](#env_definitionyml)
  - [`config.yml`](#configyml)
  - [`deployer.yml`](#deployeryml)
  - [`integration.yml`](#integrationyml)
  - [`registry.yml`](#registryyml)
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

Located in the Instance repository at: `/configuration/<cluster-name>/<env-name>/Inventory/env_definition.yml`  
Pass the `<cluster-name>/<env-name>` to the [`ENV_NAMES`](https://github.com/Netcracker/qubership-envgene/blob/main/docs/instance-pipeline-parameters.md#env_names) input parameter when executing Environment operations

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
  # Used by EnvGene extensions that implement integration with various CMDB systems
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

```yaml
crypt: false
artifact_definitions_discovery_mode: auto|true|false
cloud_passport_decryption: true
app_reg_def_mode: auto|cmdb|local
```

## `deployer.yml`

TBD

## `integration.yml`

TBD

## `registry.yml`

TBD

## Artifact Definition

TBD
