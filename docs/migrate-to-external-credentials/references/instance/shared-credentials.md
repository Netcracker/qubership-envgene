# Shared Credentials

Policy: [credential-policy.md](credential-policy.md) (read before convert).

## Find files

Canonical paths:

- Repository Shared: `environments/credentials/*.yml` → `external-tier`, create proposal `false`,
  path `external` or approved shared path.
- Cluster Shared: `environments/<cluster>/credentials/*.yml` → same as repository Shared.
- Environment Shared: `environments/<cluster>/<env>/Inventory/credentials/*.yml` → `env-tier`,
  create proposal `true`, path `<cluster>/<environment>`.

Some repositories use `environments/<cluster>/shared-credentials/` instead of
`environments/<cluster>/credentials/` - treat as cluster Shared.

Collect from `envTemplate.sharedMasterCredentialFiles`. Orphaned files (no consumer references any
`credId` from the file): delete via cleanup, do not convert.

Warn if many consumers share one file.

## Apply

Confirm decision records from `classify_credentials.py`. Convert only confirmed entries via
`convert_credential_files.py --decisions-json`. Fix extensions with `fix_shared_master_refs.py`.

Keeping an existing value: plan `proposedCreate: false` + `writeToStore: true` (plan only).

Shapes: [transforms.md](transforms.md).
