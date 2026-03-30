# SBOM_TEST - Open source PostgreSQL example

- [Description](#description)
- [Layout in an Instance Repository](#layout-in-an-instance-repository)
- [Pipeline variables (Generate Effective Set)](#pipeline-variables-generate-effective-set)
- [Templates](#templates)
- [Env template chain (SD + SBOM)](#env-template-chain-sd--sbom)
- [Files](#files)

## Description

This folder contains a **minimal** Application SBOM, Solution Descriptor (SD), and Solution SBOM aligned with:

- `schemas/application.sbom.schema.json` (Application SBOM)
- Test layout under `build_effective_set_generator/effective-set-generator/src/test/resources/environments/cluster-01/pl-01/`
- Instance pipeline expectations in `github_workflows/instance-repo-pipeline/.github/workflows/Envgene.yml`

## Layout in an Instance Repository

The `generate_effective_set` job passes:

- `--sboms-path=${CI_PROJECT_DIR}/sboms`
- `--sd-path=${CI_PROJECT_DIR}/environments/<cluster>/<env>/Inventory/solution-descriptor/sd.yaml`

Place files as follows (example environment `demo-cluster/demo-env`):

```text
configuration/registry.yml
sboms/postgres/postgres-<VERSION-WITH-COLONS-AS-DASHES>.sbom.json
environments/demo-cluster/demo-env/Inventory/solution-descriptor/sd.yaml
environments/demo-cluster/demo-env/Inventory/solution-descriptor/solution.sbom.json
```

**SBOM file name rule (Effective Set Generator):** for `applications[].version` `postgres:16.4-oss-1`, the CLI loads `sboms/postgres/postgres-16.4-oss-1.sbom.json` (application name from the part before `:`, file base = full version string with `:` replaced by `-`).

The Application SBOM uses `registry_id=registry-1` and Maven/Docker `repository_id` values that must exist in `configuration/registry.yml` (see `SBOM_TEST/configuration/registry.yml`). Purls must match the patterns expected by the generator (`pkg:maven/...?registry_id=...&repository_id=...`, `pkg:docker/...?registry_id=...&repository_id=...`).

Use the **same** `postgres:<VERSION>` string in `sd.yaml` as in the Solution SBOM `name` + `version` (see `postgres/sd.yaml`).

## Pipeline variables (Generate Effective Set)

| Variable                 | Example value           | Notes                               |
|--------------------------|-------------------------|-------------------------------------|
| `ENV_NAMES`              | `demo-cluster/demo-env` | Target environment                  |
| `GENERATE_EFFECTIVE_SET` | `true`                  | Enables the job                     |
| `ENV_BUILDER`            | `true` or `false`       | `false` if instance already built   |
| `ENV_TEMPLATE_VERSION`   | `env-template:x.y.z`    | When building instance              |
| `SD_SOURCE_TYPE`       | `artifact` or `json`    | How SD is provided                  |
| `SD_VERSION` / `SD_DATA` | (empty)                 | Optional if `sd.yaml` is in the repo |

If SD is already committed as `sd.yaml`, you can omit `SD_*` variables and rely on the file in the repository.

## Templates

Under `templates/` you will find placeholders (`{{ ... }}`) to adapt registry, versions, and image coordinates for other open source stacks.

## Env template chain (SD + SBOM)

EnvGene fills `current_env.solution_structure` from the SD and rendered namespaces; Jinja in the **environment template** references keys `<ApplicationName>` and `<deployPostfix>` from the SD. The Effective Set step uses the same SD plus Application SBOMs under `sboms/`.

A minimal template aligned with `postgres/sd.yaml` (`postgres` + `deployPostfix: pg`) lives under:

- `env_templates/postgres-oss-template.yaml` (root)
- `env_templates/postgres-oss/` (tenant, cloud, `Namespaces/pg.yml.j2`)
- `resource_profiles/dev_postgres_oss.yaml` (profile used by `pg.yml.j2`)

See [env_templates/CHAIN.md](env_templates/CHAIN.md) for the full rules and the parallel with `test_data/test_templates`.

## Files

| Path                                       | Description                                                    |
|--------------------------------------------|----------------------------------------------------------------|
| `postgres/postgres-16.4-oss-1.sbom.json`   | Application SBOM (`library/postgres:16-alpine`, digest amd64) |
| `configuration/registry.yml`               | Minimal `registry-1` for SBOM purls                            |
| `postgres/sd.yaml`                         | Solution Descriptor (one application)                          |
| `postgres/solution.sbom.json`              | Solution SBOM referencing the Application SBOM                 |
| `templates/*.template`                     | Placeholders for SBOM / SD                                    |
| `env_templates/postgres-oss-template.yaml` | Root env template (`postgres` / `pg`)                        |
| `env_templates/CHAIN.md`                   | SD ↔ env template ↔ SBOM                                      |
| `resource_profiles/dev_postgres_oss.yaml`  | Resource profile for `postgres-oss` namespace template         |

The container hash is the **linux/amd64** digest for `library/postgres:16-alpine` from Docker Hub (update if you change tag or architecture).

To disable Helm chart checks instead of including `application/vnd.qubership.app.chart`, set `EFFECTIVE_SET_CONFIG` with `"app_chart_validation": "false"` (see instance pipeline docs).
