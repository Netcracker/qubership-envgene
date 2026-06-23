# Worked example: template and instance repositories

A complete, consistent pair of repositories produced by [Migrate CMDB environments to
EnvGene](/docs/cmdb-migration/migrate-cmdb-to-envgene.md). Study it end to end, then map the names to your own
project.

## Scenario

- One cluster, `cluster-01`, holding one environment, `env-1`.
- One composite environment type: baseline namespace `core` with satellites `bss` and `oss`.
- Template artifact `bss-template:1.0.0`, built from the `composite` descriptor.

## Layout

`template-repository/` holds the template:

- `templates/env_templates/composite.yaml` the descriptor for the composite type.
- `templates/env_templates/common/` the shared tenant, cloud, and composite structure templates.
- `templates/env_templates/namespaces/` one namespace template per `deployPostfix`: `core`, `bss`, `oss`.
- `templates/appdefs/` and `templates/regdefs/` the Application and Registry Definitions the template needs.

`instance-repository/` holds the inventory:

- `environments/cluster-01/cloud-passport/` the Cloud Passport and its credential file.
- `environments/cluster-01/env-1/Inventory/env_definition.yml` the Environment Inventory.
- `environments/cluster-01/env-1/Inventory/parameters/` the migrated ParameterSets.
- `environments/cluster-01/env-1/Inventory/resource_profiles/` the migrated Resource Profile Override.
- `environments/credentials/shared-credentials.yml` the repository-wide shared credentials.
- `configuration/artifact_definitions/bss-template.yaml` the Artifact Definition for the template artifact.
- `configuration/credentials/credentials.yml` the system credential the Artifact Definition uses.

## How the two repositories line up

- `env_definition.yml` `envTemplate.name: composite` matches the `composite.yaml` descriptor.
- `env_definition.yml` `envTemplate.artifact: bss-template:1.0.0` matches the Artifact Definition `name:
  bss-template`.
- The namespaces `core`, `bss`, `oss` match the descriptor `namespaces` and the composite structure baseline and
  satellites.
- Every ParameterSet and Resource Profile Override named in `env_definition.yml` exists under `Inventory/`.
- `sharedMasterCredentialFiles: [shared-credentials]` matches `environments/credentials/shared-credentials.yml`,
  which holds the `bss-admin-cred` referenced from `bss-deploy.yml`.
