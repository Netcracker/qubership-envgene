# Secret Store

Read before configuring `configuration/secret-stores.yml`.

## Rules

- Migration assumes **one** Secret Store per repository (`default_store`).
- Credential entries **must** set `secretStore` explicitly (usually `default_store`). EnvGene does
  not fill schema defaults and Effective Set uses `getSecretStore()` as-is.
- Do not store tokens or keys in Git.
- Do not convert Credential files while only configuring the store.
- CI/CD auth variables for the store stay outside Git.

## Existing file

Path: `configuration/secret-stores.yml`

- Only `default_store` → reuse it.
- Several stores → **ask** which id is the migration target, or consolidate to one store before
  cutover. Do not choose silently.
- Missing → ask type and required fields, then create.

## Required fields by type (ask user)

| type | Required fields |
|------|-----------------|
| `vault` | `mountPath` (and other Vault fields they use) |
| `gcp` | `projectId` |
| `aws` | `region` |
| `azure` | `vaultName` |

Minimal example (GCP):

```yaml
default_store:
  type: gcp
  projectId: <project-id>
```

## Done check

- File exists and parses as YAML
- `default_store` is defined for migration
- No secrets in the file
