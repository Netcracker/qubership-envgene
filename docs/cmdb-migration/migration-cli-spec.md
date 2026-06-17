# Migration CLI specification

- [Migration CLI specification](#migration-cli-specification)
  - [Purpose](#purpose)
  - [`migrate`](#migrate)
  - [`create-template-appdef`](#create-template-appdef)
  - [`collect-app-reg-defs`](#collect-app-reg-defs)
  - [`export-credentials`](#export-credentials)

## Purpose

This document specifies a CLI that automates the migration of CMDB environments to EnvGene. It is the task
statement for the developer who builds the CLI, and the reference an operator follows to run a migration.

The CLI reads a CMDB file export and writes EnvGene template and instance repository content. Three steps are
exposed as standalone CLI, because they are useful on their own, outside a migration:

| CLI                      | Role                                                       |
|--------------------------|------------------------------------------------------------|
| `create-template-appdef` | Registers the env-template artifact in a cloud CMDB        |
| `collect-app-reg-defs`   | Assembles AppDefs and RegDefs for a template               |
| `export-credentials`     | Exports the credential store into one shared file          |

The `migrate` runs the full flow and invokes those three as part of it.

## `migrate`

Reads the export and writes template and instance repository content in one run. It runs start to finish without
stopping for input: it migrates what it can and records the rest in the report.

Preconditions, done by the operator before the run:

- The export holds only the Clouds and Namespaces to migrate. Remove stale ones first, the CLI migrates
  everything it finds.

Inputs:

| Flag              | Description                                  |
|-------------------|----------------------------------------------|
| `--config <path>` | Path to the migration config. See below.     |

Config file (`migration.yml`):

```yaml
# CMDB file export to migrate
cmdbExport: ./cmdb-export
# Shared template repository
templateRepo: ./template-repo
# Instance repository per region, keyed by region name
instanceRepos:
  region-a: ./instance-repo-a
  region-b: ./instance-repo-b
# Region every cluster routes to until the cluster-URL-to-region rule is defined
defaultInstanceRepo: ./instance-repo-a
```

Steps:

1. Group environments into types by their Full Solution Descriptor.
2. Build one template per type: namespace templates per `deployPostfix`, cloud and tenant templates, the
   template descriptor, and the composite structure when the export has one.
3. Run `collect-app-reg-defs` for the applications the templates need.
4. Run `create-template-appdef` for the env-template artifact.
5. Deduplicate clusters by `apiUrl`. Create one cluster folder and one Cloud Passport per cluster.
6. For each environment, create the inventory and set its template name and artifact.
7. Attach cloud and namespace parameters: inline, referenced ParameterSets, and per-application parameters from
   Application objects.
8. Attach cloud and namespace Resource Profile Overrides from the exported profiles.
9. Add the Full Solution Descriptor and the Artifact Definition.
10. Run `export-credentials` and reference the shared file from every inventory.
11. Write the migration report.

Outputs:

- Template repository content: env templates, descriptors, AppDefs, RegDefs, composite structures.
- Instance repository content per region: cluster folders, Cloud Passports, inventories, ParameterSets, resource
  profiles, Solution Descriptors, Artifact Definitions, and the shared credential file.
- The migration report: what was created, what was skipped, and what was flagged for review. The operator
  finishes those by hand after the run.

## `create-template-appdef`

Creates an Application Definition for the env-template artifact in a CMDB.

Inputs:

| Flag                        | Description                                       |
|-----------------------------|---------------------------------------------------|
| TBD                         |                                                   |

Steps:

1. Build the Application Definition for the artifact.
2. Create it in the target cloud CMDB.

Outputs:

- The Application Definition in the target cloud CMDB.

> [!NOTE]
> The detailed behavior of this CLI is not yet defined.

## `collect-app-reg-defs`

Assembles the Application and Registry Definitions a template needs, with a parameterized registry.

Inputs:

| Flag                       | Description                                                     |
|----------------------------|-----------------------------------------------------------------|
| `--sd <path>`              | Full Solution Descriptor to read applications from. Repeatable. |
| `--definitions-repo <url>` | Centralized definitions repository. Optional, has a default.    |
| `--template-repo <path>`   | Target template repository.                                     |

Steps:

1. For each application, take its base AppDef from the centralized definitions repository.
2. Collect the RegDefs those AppDefs reference.
3. Write each AppDef to `templates/appdefs/<application-name>.yml.j2` and each RegDef to
   `templates/regdefs/<registry-name>.yml.j2`.
4. Replace each hardcoded `registryName` with `{{ appdefs.overrides.registryName | default('<original>') }}`.

Outputs:

- AppDef and RegDef template files in the template repository.

## `export-credentials`

Exports every credential from the credential store into one EnvGene shared credential file.

Inputs:

| Flag                       | Description                                      |
|----------------------------|--------------------------------------------------|
| TBD                        |                                                  |

Steps:

1. Read every credential from the store.
2. Map each one to an EnvGene Credential.
3. Write them to a single shared credential file.

Outputs:

- One shared credential file.

> [!NOTE]
> The credential export mechanism is not yet defined.
