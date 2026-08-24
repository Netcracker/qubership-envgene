# Secret Store

Read before configuring `configuration/secret-stores.yml`.

## Rules

- Do not store tokens or keys in Git.
- Do not convert Credential files while only configuring the store.
- Store id must match `[A-Za-z_][A-Za-z0-9_]*`. Prefer `default_store`.
- CI/CD auth variables for the store stay outside Git.

## Existing file

Path: `configuration/secret-stores.yml`

- One store or only `default_store` → reuse it.
- Several stores → **ask which id to use** for migration. Do not choose silently.
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
- Every store id the migration will reference is defined
- No secrets in the file
