# Env template ↔ SD ↔ SBOM chain (SBOM_TEST)

- [How test_data templates use the Solution Descriptor](#how-test_data-templates-use-the-solution-descriptor)
- [This folder (postgres-oss)](#this-folder-postgres-oss)
- [Example env_definition snippet](#example-env_definition-snippet)

## How test_data templates use the Solution Descriptor

1. **Solution Descriptor** (`Inventory/solution-descriptor/sd.yaml`) lists applications:

   - `version` is `ApplicationName:VersionString` (one `:`).
   - `deployPostfix` is the namespace role key (must match a folder under `Namespaces/<deployPostfix>/` in the generated instance and a `deploy_postfix` entry in the **root env template YAML**).

2. **At render time**, EnvGene builds `current_env.solution_structure` from the SD and the **already rendered** namespace objects:

   - `current_env.solution_structure['<ApplicationName>']['<deployPostfix>'].namespace`
   - `current_env.solution_structure['<ApplicationName>']['<deployPostfix>'].version`

   See [template-macros.md](/docs/template-macros.md#current_envsolution_structure).

3. **Root env template** (e.g. `test_data/test_templates/env_templates/test-solution-structure-template.yaml`) declares:

   - `tenant`, `cloud`, optional `bg_domain`
   - `namespaces:` with `template_path` and **`deploy_postfix`** for each namespace slice.

   The value of `deploy_postfix` must equal the corresponding `deployPostfix` in the SD. Example: SD has `deployPostfix: app-core` and `Test-App-DB-Name:…` → template has `deploy_postfix: "app-core"` and Jinja uses `current_env.solution_structure["Test-App-DB-Name"]["app-core"]`.

4. **Application SBOM** is **not** read by Jinja. It is consumed by the Effective Set Generator (`--sboms-path`) together with the SD. Consistency rules:

   - SD `ApplicationName` (part before `:`) = SBOM metadata component `name` and Solution SBOM application `name`.
   - SD `deployPostfix` = namespace `deploy_postfix` in the env template = Inventory namespace folder for that app.
   - SBOM file path: `sboms/<appName>/<sdVersionWithColonsAsDashes>.sbom.json` (see SBOM_TEST README).

## This folder (`postgres-oss`)

| Piece | SBOM_TEST path | Matches |
|-------|----------------|---------|
| SD | `postgres/sd.yaml` | `postgres:16.4-oss-1`, `deployPostfix: pg` |
| Env template root | `env_templates/postgres-oss-template.yaml` | `deploy_postfix: "pg"` |
| Namespace Jinja | `env_templates/postgres-oss/Namespaces/pg.yml.j2` | Uses `solution_structure['postgres']['pg']` |
| Resource profile | `resource_profiles/dev_postgres_oss.yaml` | Referenced by `profile.name` in `pg.yml.j2` |

Copy `resource_profiles/dev_postgres_oss.yaml` into your template artifact next to other `resource_profiles/` if you use this profile name.

## Example env_definition snippet

Point `envTemplate.name` and `templateArtifact` at the artifact that contains this `env_templates/` tree (same layout as `test_data/test_templates` in a published template package):

```yaml
envTemplate:
  name: "postgres-oss-template"
  templateArtifact:
    registry: "<your-registry>"
    repository: "<your-repo>"
    artifact:
      group_id: "org.example.oss"
      artifact_id: "postgres-oss-env-template"
      version: "0.1.0"
```

The published artifact must include `env_templates/postgres-oss-template.yaml` at the repo root layout expected by EnvGene (see [Environment template](/docs/envgene-objects.md)).
