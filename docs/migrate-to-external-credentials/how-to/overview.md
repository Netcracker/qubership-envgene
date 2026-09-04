# Migrate to External Credentials: overview

- [Who does what](#who-does-what)
- [Prerequisites](#prerequisites)
- [Flow](#flow)
  - [1. Template Repository](#1-template-repository)
  - [2. Choose where passwords and tokens live](#2-choose-where-passwords-and-tokens-live)
  - [3a. Values in the Instance Repository](#3a-values-in-the-instance-repository)
  - [3b. Values in Jenkins](#3b-values-in-jenkins)
  - [4. After the Store is filled](#4-after-the-store-is-filled)
- [Next how-tos](#next-how-tos)

## Who does what

| Action | Owner |
|--------|-------|
| Clone, branch, commit, MR, merge, publish Template | You |
| Template / Instance YAML cutover | Migration skills (or you, following the how-tos) |
| Run Instance pipeline / deploy | You |
| Read actual passwords and tokens from Git (`collect`) or Jenkins (`export-credentials`) | [migration-cli](../cli/README.md) |
| Match those values into External Credential Context (`fill`) | migration-cli |
| Write secrets into the Secret Store | [external-cred-provision](/docs/features/external-creds-provisioning-cli.md) |

Skills do not clone, commit, run pipeline, handle actual passwords and tokens, or write the Secret
Store.

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
- Skills pack: [../skills/](../skills/)
- CLI installed: `pip install -e docs/migrate-to-external-credentials/cli` (add `[decrypt]` for Fernet)

Migration also needs Instance pipeline parameter `EXTERNAL_CREDENTIAL_PROVISIONING` with values
`apply` (default) and `skip`. Use `skip` on the first Effective Set run so the job emits External
Credential Context without calling `external-cred-provision` in the pipeline. After you transfer
secrets with migration-cli + the provisioning CLI, run Effective Set again with `apply` (or omit the
parameter).

Always set `secretStore` on external Credential entries (usually `default_store`). JSON Schema
documents a default, but the Effective Set calculator reads the field as-is with no runtime
fallback.

## Flow

```text
Template cutover (skill) → publish Template version
        ↓
Where do actual passwords and tokens live today?
   ├─ Instance Repository  →  3a
   └─ Jenkins CMDB         →  3b
        ↓
Effective Set with EXTERNAL_CREDENTIAL_PROVISIONING=apply → test deploy → remaining envs
```

### 1. Template Repository

Run Template YAML cutover with skill `migrate-template-repository` (see
[Migrate Template Repository](migrate-template-repository.md) and
[skills/template-repository/](../skills/template-repository/)).

Publish a concrete Template version that registers `external_credential_template`.

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
1. migration-cli collect
        ↓
2. Instance YAML cutover (skill migrate-instance-repository) → MR/merge
        ↓
3. Instance pipeline on a test env:
     GENERATE_EFFECTIVE_SET=true
     EXTERNAL_CREDENTIAL_PROVISIONING=skip
   → Effective Set + External Credential Context (no Store write in-pipeline)
        ↓
4. migration-cli fill  (match collected values into Context)
        ↓
5. external-cred-provision  (write secrets into the Secret Store)
        ↓
6. Instance pipeline again with EXTERNAL_CREDENTIAL_PROVISIONING=apply (default)
```

Details: [Transfer secrets to the Secret Store](transfer-secrets-to-store.md) and
[Migrate Instance Repository](migrate-instance-repository.md).

### 3b. Values in Jenkins

Do **not** run `collect` against the Instance Repository. Export from Jenkins after the first
Effective Set run that produces Context.

```text
1. Instance YAML cutover (skill migrate-instance-repository) → MR/merge
        ↓
2. Instance pipeline on a test env:
     GENERATE_EFFECTIVE_SET=true
     EXTERNAL_CREDENTIAL_PROVISIONING=skip
   → Effective Set + External Credential Context (no Store write in-pipeline)
        ↓
3. migration-cli export-credentials  (from Jenkins)
        ↓
4. migration-cli fill  (match Jenkins export into Context)
        ↓
5. external-cred-provision  (write secrets into the Secret Store)
        ↓
6. Instance pipeline again with EXTERNAL_CREDENTIAL_PROVISIONING=apply (default)
```

### 4. After the Store is filled

Remove any leftover Credential `data` from Git if it is still present. Run a test deploy on the
test environment, then repeat for remaining environments.

Do not commit `collect` / `export-credentials` / `fill` outputs to Git.

## Next how-tos

1. [Migrate Template Repository](migrate-template-repository.md)
2. [Migrate Instance Repository](migrate-instance-repository.md)
3. [Transfer secrets to the Secret Store](transfer-secrets-to-store.md)
