# System Credentials

Policy: [credential-policy.md](credential-policy.md) (read before convert).

## Locate

```text
configuration/credentials/credentials.yml
environments/<cluster>/app-deployer/deployer-creds.yml
```

Also macros in `configuration/deployer.yml` / `configuration/integration.yml`.

## Rules

- `tier: external-tier`, scope `system`.
- `create` always false in plan / omitted in YAML. Never `create: true`.
- Path: approved system path; fallback `external` (confirm with user).
- Vault and GCP only for System Secret Stores (How-to).
- Transfer/provision before removing `data`.
- `credentialsId` in Artifact/Registry stays a plain string.

## Apply

Confirmed decisions only → `convert_credential_files.py --decisions-json` then
`replace_macros.py` on config files.

Shapes: [transforms.md](transforms.md).
