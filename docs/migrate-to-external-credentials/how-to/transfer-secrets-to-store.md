# Transfer secrets to the Secret Store

- [Description](#description)
- [Install](#install)
- [When to use which command](#when-to-use-which-command)
- [Collect from the Instance Repository](#collect-from-the-instance-repository)
- [Export from Jenkins](#export-from-jenkins)
- [Fill External Credential Context](#fill-external-credential-context)
- [Provision into the Secret Store](#provision-into-the-secret-store)
- [See also](#see-also)

## Description

Use [migration-cli](../cli/README.md) only to move actual passwords and tokens during migration.
It does not convert Credential YAML to `type: external`. That is the skills / Instance how-to.

Follow the path in [overview Flow](overview.md#flow):

- **Values in the Instance Repository:** run `collect` **before** Instance YAML cutover, then after
  Effective Set with `EXTERNAL_CREDENTIAL_PROVISIONING=skip`, run `fill` and
  `external-cred-provision`.
- **Values in Jenkins:** skip `collect`. After Effective Set with `skip`, run
  `export-credentials`, then `fill` and `external-cred-provision`.

`fill` writes those values into Context entries with `strategy: fail_if_absent`.
`create_if_absent` entries are skipped by `fill` - EnvGene / provision generates them.

Do not commit collect/export/fill outputs to Git.

## Install

```bash
cd docs/migrate-to-external-credentials/cli
pip install -e .
pip install -e ".[decrypt]"   # Fernet field-level decryption
```

Full command reference: [migration-cli README](../cli/README.md).

## When to use which command

| Source of passwords and tokens | Command | When |
|--------------------------------|---------|------|
| Still in Instance Credential files (encrypted or plain) | `collect` | Before Instance YAML cutover |
| In Jenkins CMDB / Cloud Deployer | `export-credentials` | After Context exists (`skip` ES run) |
| Match into Context for provision | `fill` | After Context + values file/dir exist |

## Collect from the Instance Repository

```bash
export SECRET_KEY='...'   # if Fernet-encrypted fields
migration-cli collect \
  --instance-root /path/to/instance-repo \
  --out /tmp/cred-values.yaml
```

Optional: `--env-filter cluster/env1,cluster/env2`.

`collect` ignores `type: external` entries. Run it while Credentials are still local.

## Export from Jenkins

```bash
export CLOUD_USERNAME='...'
export CLOUD_TOKEN='...'
migration-cli export-credentials \
  --tenant TENANT \
  --out-dir ./cmdb-export-credentials
```

## Fill External Credential Context

From collect output (whole repo Context scan):

```bash
migration-cli fill \
  --repo-root /path/to/instance-repo \
  --values /tmp/cred-values.yaml \
  --values-format instance_scoped \
  --out /tmp/filled-all-environments.yaml
```

From Jenkins exports:

```bash
migration-cli fill \
  --repo-root /path/to/instance-repo \
  --values-dir ./cmdb-export-credentials \
  --values-format jenkins_export \
  --out /tmp/filled-all-environments.yaml \
  --continue-on-error
```

## Provision into the Secret Store

```bash
external-cred-provision /tmp/filled-all-environments.yaml
```

Configure store auth env vars as in the
[provisioning CLI](/docs/features/external-creds-provisioning-cli.md#environment-variables).

Then re-run the Instance pipeline with `EXTERNAL_CREDENTIAL_PROVISIONING=apply` (default).

## See also

- [Overview](overview.md)
- [Migrate Instance Repository](migrate-instance-repository.md)
- [migration-cli README](../cli/README.md)
- [External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md)
