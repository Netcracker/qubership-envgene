# Migrate to External Credentials: overview

- [Who does what](#who-does-what)
- [Prerequisites](#prerequisites)
- [Flow](#flow)
  - [1. Template Repository](#1-template-repository)
  - [2. Choose where passwords and tokens live](#2-choose-where-passwords-and-tokens-live)
  - [3a. Values in the Instance Repository](#3a-values-in-the-instance-repository)
  - [3b. Values in Jenkins](#3b-values-in-jenkins)
  - [4. After the Store is filled](#4-after-the-store-is-filled)
- [Next modes](#next-modes)

## Who does what

| Action | Performed by |
|--------|--------------|
| Clone, branch, commit, MR, merge, publish Template | User |
| Template / Instance YAML cutover | Agent skill mode `template` / `instance` |
| Run Instance pipeline / deploy | User |
| Read / match passwords and tokens (`collect` / `export` / `fill`) | [migration-cli](../cli/README.md) via mode `transfer` |
| Write secrets into the Secret Store | [external-cred-provision](/docs/features/external-creds-provisioning-cli.md) |

> [!IMPORTANT]
> Do not remove Credential `data` from Git until you have collected it (Instance path) or until the
> secret exists in the Secret Store (or `create: true` is intentional and a new generated value is
> acceptable). `migration-cli collect` skips `type: external` entries - collect before Instance YAML
> cutover while passwords and tokens still live in the Instance Repository.

## Prerequisites

- EnvGene version that supports External Credentials
- Instance Repository on the No-CMDB path for deployer credentials
- One `default_store` in `configuration/secret-stores.yml`
- Store auth CI/CD variables configured for your store type
- For Jenkins export: Jenkins API credentials (see migration-cli README)
- Instance pipeline parameter `EXTERNAL_CREDENTIAL_PROVISIONING` available (`apply` default, `skip`
  for the first run - see [Flow](#flow))
- CLI: `pip install -e docs/migrate-to-external-credentials/cli` (add `[decrypt]` for Fernet)

## Flow

```text
Template cutover (mode template) → publish Template version
        ↓
Where do actual passwords and tokens live today?
   ├─ Instance Repository  →  3a
   └─ Jenkins CMDB         →  3b
        ↓
Effective Set with EXTERNAL_CREDENTIAL_PROVISIONING=apply → test deploy → remaining envs
```

### 1. Template Repository

Follow [mode-template.md](mode-template.md). Publish a concrete Template version that registers
`external_credential_template`.

### 2. Choose where passwords and tokens live

| Source today | Path |
|--------------|------|
| Local Credential `data` still in the Instance Repository (Git) | [3a](#3a-values-in-the-instance-repository) |
| Values only in Jenkins CMDB / Cloud Deployer | [3b](#3b-values-in-jenkins) |

You need the actual passwords and tokens for every Credential that will omit `create`
(`create: false` in the plan / `writeToStore: true`). EnvGene-generated secrets (`create: true`) do
not need transfer.

### 3a. Values in the Instance Repository

Collect **before** Instance YAML cutover. After convert, entries are `type: external` and
`collect` no longer reads them.

```text
1. migration-cli collect  (mode transfer)
        ↓
2. Instance YAML cutover → MR/merge  (mode instance)

        ↓
3. Instance pipeline on a test env:
     GENERATE_EFFECTIVE_SET=true
     EXTERNAL_CREDENTIAL_PROVISIONING=skip
   → Effective Set + External Credential Context (no Store write in-pipeline)
        ↓
4. migration-cli fill  (mode transfer)
        ↓
5. external-cred-provision  (write secrets into the Secret Store)
        ↓
6. Instance pipeline again with EXTERNAL_CREDENTIAL_PROVISIONING=apply (default)
```

Details: [mode-transfer.md](mode-transfer.md) and [mode-instance.md](mode-instance.md).

### 3b. Values in Jenkins

Do **not** run `collect` against the Instance Repository. Export from Jenkins after the first
Effective Set run that produces Context.

```text
1. Instance YAML cutover → MR/merge  (mode instance)

        ↓
2. Instance pipeline on a test env:
     GENERATE_EFFECTIVE_SET=true
     EXTERNAL_CREDENTIAL_PROVISIONING=skip
   → Effective Set + External Credential Context (no Store write in-pipeline)
        ↓
3. migration-cli export-credentials  (mode transfer)
        ↓
4. migration-cli fill  (mode transfer)
        ↓
5. external-cred-provision
        ↓
6. Instance pipeline again with EXTERNAL_CREDENTIAL_PROVISIONING=apply (default)
```

### 4. After the Store is filled

Remove any leftover Credential `data` from Git if it is still present. Run a test deploy on the
test environment, then repeat for remaining environments.

Do not commit `collect` / `export-credentials` / `fill` outputs to Git.

## Next modes

1. [mode-template.md](mode-template.md)
2. [mode-transfer.md](mode-transfer.md) - `collect` first if values are still in Git
3. [mode-instance.md](mode-instance.md)
4. [mode-transfer.md](mode-transfer.md) - `fill` / provision after Effective Set with `skip`
