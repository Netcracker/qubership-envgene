# System Credentials

Policy: [credential-policy.md](credential-policy.md) (read before convert).

## Locate

```text
configuration/credentials/credentials.yml
```

Also macros in `configuration/integration.yml` and `configuration/registry.yml`.

`environments/<cluster>/app-deployer/deployer-creds.yml` is **out of scope** for No-CMDB
repositories - delete during cleanup, do not convert.

## Rules

- `tier: external-tier`, scope `system`.
- `create` always false in plan / omitted in YAML. Never `create: true`.
- Path: approved system path; fallback `external` (confirm with user).
- Vault and GCP only for System Secret Stores (How-to).
- `writeToStore: true` transfer before removing `data`.
- `credentialsId` in Artifact/Registry stays a plain string.
- Always set `secretStore: default_store` on credential entries (or another confirmed store id).

## Apply

Confirmed decisions only → `convert_credential_files.py --decisions-json` then
`replace_macros.py` on config files.

Shapes: [transforms.md](transforms.md).
