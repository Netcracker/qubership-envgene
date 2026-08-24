# Generate External Credential Context for migration

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Default store paths](#default-store-paths)
- [Steps](#steps)
  - [Install the CLI](#install-the-cli)
  - [Run the CLI](#run-the-cli)
  - [Review the report](#review-the-report)
  - [Provision secrets](#provision-secrets)
- [Results](#results)
- [See also](#see-also)

## Description

Build an External Credential Context YAML from local Credentials in an Instance Repository, then
pass that file to `external-cred-provision`.

Do this **before** you convert Credential YAML to `type: external`. After cutover, EnvGene no longer
reads values from Git. The Context file is the input that copies current plaintext into the Secret
Store at the same VALS paths Effective Set will emit later.

The CLI does not write to the Secret Store, does not change Git, and does not call
`external-cred-provision`.

## Prerequisites

- Python 3.12
- An Instance Repository whose Credentials are still local (`usernamePassword` or `secret`)
- You know the Secret Store id, type, and type-specific field (Vault `mountPath`, GCP `projectId`,
  AWS `region`, or Azure `vaultName`)
- For Fernet-encrypted values: `SECRET_KEY` in the process environment
- For SOPS-encrypted files: the `sops` CLI on `PATH`, and `SOPS_AGE_KEY` or
  `ENVGENE_AGE_PRIVATE_KEY`

## Default store paths

When you omit `--remote-ref-path-template`, the CLI uses the same prefixes as
[Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md).
`credId` is not part of the prefix. The CLI appends it the same way Effective Set does.

| Source                         | Default prefix             |
|--------------------------------|----------------------------|
| Cloud Passport                 | `<cluster>`                |
| Environment-level Shared       | `<cluster>/<environment>`  |
| Cluster or repository Shared   | `external`                 |
| System Credentials             | `external`                 |

Use these same prefixes as `remoteRefPath` when you convert YAML later. If you pass
`--remote-ref-path-template`, use that rendered prefix as `remoteRefPath` instead.

Placeholders in a template: `{{ cloud }}` (cluster folder) and `{{ env }}` (environment folder).

## Steps

### Install the CLI

From a clone of this repository:

```bash
pip install ./python/external-cred-migration
```

The command is `external-cred-migrate`. Also install
[qubership-external-cred-provision](/python/external-cred-provision/) so you can provision in the
last step.

### Run the CLI

Vault example for one Environment Instance:

```bash
external-cred-migrate \
  --instance-repo /path/to/instance-repository \
  --secret-store default_store \
  --store-type vault \
  --mount-path secret \
  --env cluster-1/env-1 \
  --output /path/to/external-credentials-context.yaml
```

GCP example for the whole repository:

```bash
external-cred-migrate \
  --instance-repo /path/to/instance-repository \
  --secret-store default_store \
  --store-type gcp \
  --project-id my-project \
  --output /path/to/external-credentials-context.yaml
```

Optional flags:

- `--dry-run` - print the report, do not write the file
- `--remote-ref-path-template "{{ cloud }}/{{ env }}"` - one prefix for every Credential

The CLI reads Cloud Passport `*-creds.yml`, Shared Credential files, and System Credentials. It
does not read generated `environments/<cluster>/<env>/Credentials/credentials.yml`. Stubs
(`envgeneNullValue`, empty values) are omitted.

If one `credId` maps to different store paths in different environments, the CLI writes one file
per environment next to `--output`, named `{stem}.{cluster}-{env}{suffix}`.

> [!WARNING]
> Do not commit the Context file. It contains plaintext secrets.

### Review the report

The console lists each included `credId`, its source file, path prefix, and VALS URI. Skipped
entries show a reason (stub, already external). Passwords are not printed.

Confirm the VALS paths match the `remoteRefPath` values you will write during YAML cutover.

### Provision secrets

```bash
external-cred-provision /path/to/external-credentials-context.yaml
```

Dry-run first if you want store checks without writes:

```bash
external-cred-provision --dry-run /path/to/external-credentials-context.yaml
```

See [External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md).

## Results

- A Context YAML with `strategy: overwrite` and plaintext `data` from Git
- VALS paths that match Effective Set after you convert Credentials with the same prefixes
- Secret Store unchanged until you run `external-cred-provision`
- Instance Repository unchanged

Continue with
[Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md).

## See also

- [UC-MIG-1 Migration CLI](/docs/analysis/external-credentials-migration-cli.md)
- [Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md)
- [External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md)
- [External Credentials Management](/docs/features/external-creds.md)
- [Package source](/python/external-cred-migration/)
