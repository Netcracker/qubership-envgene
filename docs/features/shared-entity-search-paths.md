# Shared entity search paths

- [Shared entity search paths](#shared-entity-search-paths)
  - [Overview](#overview)
  - [Shared template variables](#shared-template-variables)
  - [Parameter sets](#parameter-sets)
  - [Resource profiles](#resource-profiles)
  - [Cloud Passport](#cloud-passport)
  - [Shared credentials](#shared-credentials)
  - [Deployer configuration](#deployer-configuration)

## Overview

When resolving named references to shared entities during environment generation, EnvGene searches for
the corresponding files in a set of locations in the instance repository. Locations are checked in
priority order and the first match is used.

Each section below lists all search paths in priority order. The **Recommended** column identifies
the supported locations for storing new and existing files.

## Shared template variables

Referenced via `envTemplate.sharedTemplateVariables` in [`env_definition.yml`](/docs/envgene-configs.md#env_definitionyml).
See [Shared Template Variable Files](/docs/envgene-objects.md#shared-template-variable-files) for the file format.

| Priority | Path                                                               | Recommended |
|----------|-------------------------------------------------------------------|-------------|
| 1        | `/environments/<cluster-name>/<env-name>/Inventory/configuration/`  | Yes         |
| 2        | `/environments/<cluster-name>/<env-name>/Inventory/configurations/` | Yes         |
| 3        | `/environments/<cluster-name>/configuration/`                       | Yes         |
| 4        | `/environments/<cluster-name>/configurations/`                      | Yes         |
| 5        | `/environments/configuration/`                                      | Yes         |
| 6        | `/environments/configurations/`                                     | Yes         |
| 7        | `/environments/<cluster-name>/<env-name>/Inventory/`                |             |

## Parameter sets

Referenced via `envTemplate.envSpecificParamsets`, `envTemplate.envSpecificE2EParamsets`, and
`envTemplate.envSpecificTechnicalParamsets` in [`env_definition.yml`](/docs/envgene-configs.md#env_definitionyml).
See [Environment Specific ParameterSet](/docs/envgene-objects.md#environment-specific-parameterset) for the file format.

| Priority | Path                                                          | Recommended |
|----------|---------------------------------------------------------------|-------------|
| 1        | `/environments/<cluster-name>/<env-name>/Inventory/parameters/` | Yes         |
| 2        | `/environments/<cluster-name>/parameters/`                    | Yes         |
| 3        | `/environments/parameters/`                                   | Yes         |

## Resource profiles

Referenced via `envTemplate.envSpecificResourceProfiles` in [`env_definition.yml`](/docs/envgene-configs.md#env_definitionyml).
See [Environment-Specific Resource Profile Override](/docs/envgene-objects.md#environment-specific-resource-profile-override) for the file format.

| Priority | Path                                                                   | Recommended |
|----------|------------------------------------------------------------------------|-------------|
| 1        | `/environments/<cluster-name>/<env-name>/Inventory/resource_profiles/` | Yes         |
| 2        | `/environments/<cluster-name>/<env-name>/Inventory/rp_override/`       |             |
| 3        | `/environments/<cluster-name>/<env-name>/Inventory/Profiles/`          |             |
| 4        | `/environments/<cluster-name>/<env-name>/Inventory/parameters/`        |             |
| 5        | `/environments/<cluster-name>/resource_profiles/`                      | Yes         |
| 6        | `/environments/<cluster-name>/rp_override/`                            |             |
| 7        | `/environments/<cluster-name>/Profiles/`                               |             |
| 8        | `/environments/<cluster-name>/parameters/`                             |             |
| 9        | `/environments/resource_profiles/`                                     | Yes         |
| 10       | `/environments/rp_override/`                                           |             |
| 11       | `/environments/Profiles/`                                              |             |
| 12       | `/environments/parameters/`                                            |             |

## Cloud Passport

Referenced via `inventory.cloudPassport` in [`env_definition.yml`](/docs/envgene-configs.md#env_definitionyml). See
[Cloud Passport processing](/docs/features/cloud-passport-processing.md) for the full resolution behavior, including auto-association which only applies at the cluster level.

| Priority | Path                                                               | Recommended |
|----------|--------------------------------------------------------------------|-------------|
| 1        | `/environments/<cluster-name>/<env-name>/Inventory/cloud-passport/`  | Yes         |
| 2        | `/environments/<cluster-name>/<env-name>/Inventory/cloud-passports/` |             |
| 3        | `/environments/<cluster-name>/cloud-passport/`                       | Yes         |
| 4        | `/environments/<cluster-name>/cloud-passports/`                      |             |
| 5        | `/environments/cloud-passport/`                                      | Yes         |
| 6        | `/environments/cloud-passports/`                                     |             |

## Shared credentials

Referenced via `envTemplate.sharedMasterCredentialFiles` in [`env_definition.yml`](/docs/envgene-configs.md#env_definitionyml).
See [Shared Credentials File](/docs/envgene-objects.md#shared-credentials-file) for the file format.

| Priority | Path                                                                    | Recommended |
|----------|-------------------------------------------------------------------------|-------------|
| 1        | `/environments/<cluster-name>/<env-name>/Inventory/credentials/`        | Yes         |
| 2        | `/environments/<cluster-name>/<env-name>/Inventory/Credentials/`        |             |
| 3        | `/environments/<cluster-name>/<env-name>/Inventory/shared-credentials/` |             |
| 4        | `/environments/<cluster-name>/credentials/`                             | Yes         |
| 5        | `/environments/<cluster-name>/Credentials/`                             |             |
| 6        | `/environments/<cluster-name>/shared-credentials/`                      |             |
| 7        | `/environments/credentials/`                                            | Yes         |
| 8        | `/environments/Credentials/`                                            |             |
| 9        | `/environments/shared-credentials/`                                     |             |

## Deployer configuration

Loaded when `inventory.deployer` is set in [`env_definition.yml`](/docs/envgene-configs.md#env_definitionyml).
See [deployer.yml](/docs/envgene-configs.md#deployeryml) for the file format.

EnvGene first searches for a cluster-level or environment-level deployer file (priorities 1-6). If the
deployer key is not found in that file, it falls back to the global configuration file (priority 7).

| Priority | Path                                                                   | Recommended |
|----------|------------------------------------------------------------------------|-------------|
| 1        | `/environments/<cluster-name>/app-deployer/deployer.yml`               | Yes         |
| 2        | `/environments/<cluster-name>/app-deployer/app-deployer.yml`           |             |
| 3        | `/environments/<cluster-name>/cloud-deployer/deployer.yml`             |             |
| 4        | `/environments/<cluster-name>/<env-name>/app-deployer/deployer.yml`    | Yes         |
| 5        | `/environments/<cluster-name>/<env-name>/app-deployer/app-deployer.yml`|             |
| 6        | `/environments/<cluster-name>/<env-name>/cloud-deployer/deployer.yml`  |             |
| 7        | `/configuration/deployer.yml`                                          | Yes         |
