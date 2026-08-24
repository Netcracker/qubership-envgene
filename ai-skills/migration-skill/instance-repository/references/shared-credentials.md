# Shared Credentials

Policy: [credential-policy.md](credential-policy.md) (read before convert).

## Find files

- Cluster/repo Shared (`environments/<cluster>/shared-credentials/`, `environments/credentials/`)
  → `external-tier`, create proposal `false`, path `external` or approved shared path.
- Environment-level Shared (`.../<env>/Inventory/credentials/`) → `env-tier`, create proposal
  `true`, path `<cluster>/<environment>`.

Collect from `envTemplate.sharedMasterCredentialFiles`. Unbound files: ask include / skip / later.

Warn if many consumers share one file.

## Apply

Confirm decision records from `classify_credentials.py`. Convert only confirmed entries via
`convert_credential_files.py --decisions-json`. Fix extensions with `fix_shared_master_refs.py`.

Keeping an existing value: plan `proposedCreate: false` + `writeToStore: true` (plan only).

Shapes: [transforms.md](transforms.md).
