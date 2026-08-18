# Migrate Instance Repository to External Credentials

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Step 1. Inventory the Instance Repository](#step-1-inventory-the-instance-repository)
- [Step 2. Configure Secret Store](#step-2-configure-secret-store)
- [Step 3. Convert Cloud Passport Credentials and main file](#step-3-convert-cloud-passport-credentials-and-main-file)
- [Step 4. Convert Shared Credentials](#step-4-convert-shared-credentials)
- [Step 5. Convert System Credentials](#step-5-convert-system-credentials)
- [Step 6. Update environment-specific parameters](#step-6-update-environment-specific-parameters)
- [Step 7. Remove stale generated Credentials files](#step-7-remove-stale-generated-credentials-files)
- [Step 8. Validate before the pipeline](#step-8-validate-before-the-pipeline)
- [Step 9. Run the Instance pipeline](#step-9-run-the-instance-pipeline)
- [Step 10. Verify the generated result](#step-10-verify-the-generated-result)
- [Step 11. Run a test deployment](#step-11-run-a-test-deployment)
- [Rollback](#rollback)
- [See also](#see-also)

## Description

Migrate the Instance Repository from local Credentials to External Credentials.

Complete
[Migrate Template Repository to External Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md)
and publish a concrete Template version before starting here.

Do not remove `data` from any Credential YAML before its real value is already in the Secret
Store. After cutover, EnvGene no longer reads values from Git. If `create: true` is set and the
secret is missing, EnvGene generates a new value - the previous password, token, or key is lost.

Do not put secret values in Git, Merge Requests, or migration notes at any point.

### Instance rules

- After merge, every Environment Instance must use External Credentials exclusively. Mixing
  `type: external` with `type: usernamePassword` or `type: secret` in one Environment Instance is
  not supported.
- On duplicate `credId`, precedence is lowest to highest: Credential Template, then Cloud Passport,
  then Shared Credentials.
- `$type: credRef` works only in `deployParameters`, `e2eParameters`, and ParameterSets that feed
  those blocks. It does not work in `technicalConfigurationParameters`.
- Built-in string fields keep a plain `credId` string.
- CMDB import is not supported for Environment Instances with External Credentials.

## Prerequisites

Confirm before you start:

- the Instance Repository uses the No-CMDB approach
- EnvGene is upgraded to a version that supports External Credentials
- a concrete Template version with `external_credential_template` is published
- real secret values that must be kept are already in the Secret Store (stubs may wait for
  `create: true` later). Complete
  [UC-MIG-1](/docs/analysis/external-credentials-migration-cli.md) (draft) before this how-to -
  do not start YAML cutover until that transfer is done
- `/configuration/secret-stores.yml` defines every Secret Store ID you reference (Step 2)
- CI/CD authentication variables for those stores are configured
- for each Credential you know whether: the value already exists in the Secret Store (omit
  `create`), or a freshly generated value is acceptable (`create: true`)

## Step 1. Inventory the Instance Repository

Find all Environment Instances at:

```text
environments/<cluster>/<env>/Inventory/env_definition.yml
```

For each Environment Instance, record:

- `inventory.cloudPassport` - which Cloud Passport it uses
- `envTemplate.sharedMasterCredentialFiles` - which Shared Credential files it binds
- environment-specific ParameterSets
- all `credId` values referenced

Also list every Credential file:

| Location                                              | What it contains                                      |
|-------------------------------------------------------|-------------------------------------------------------|
| `environments/<cluster>/cloud-passport/*-creds.yml`   | Cloud Passport Credentials                            |
| `environments/<cluster>/cloud-passport/*.yml`         | Cloud Passport main files                             |
| `environments/<cluster>/shared-credentials/*.yml`     | Shared Credentials                                    |
| `environments/<cluster>/app-deployer/deployer-creds.yml` | Deployer System Credentials                        |
| `/configuration/credentials/credentials.yml`          | System Credentials (Git token, registry)              |
| `environments/<cluster>/<env>/Credentials/credentials.yml` | Generated files - do not edit. Delete in Step 7. |

For each local Credential (`type: usernamePassword` or `type: secret`), record:

- `credId`
- source file
- whether `data` contains a real value or a stub (`envgeneNullValue` / empty)

Include unbound files - Cloud Passport or Shared Credential files that exist but are not
referenced from any `env_definition.yml`. Convert them the same way.

**Result:** full inventory of Environment Instances, Credential sources, and per-`credId` values.

## Step 2. Configure Secret Store

Create or update `/configuration/secret-stores.yml`:

```yaml
default_store:
  type: gcp
  projectId: <project-id>
```

Supported `type` values include `vault`, `gcp`, `aws`, and `azure`. Use the fields required for
the chosen type (for example `mountPath` for Vault, `region` for AWS, `vaultName` for Azure).

The store identifier must match `[A-Za-z_][A-Za-z0-9_]*`. Configure CI/CD authentication variables
for each store. See [External Credentials Management](/docs/features/external-creds.md).

Do not store tokens or keys in Git.

**Result:** Secret Store defined.

## Step 3. Convert Cloud Passport Credentials and main file

Work through one Cloud Passport at a time: convert its `*-creds.yml` and its main file together
before moving to the next.

### Convert `*-creds.yml`

Open `environments/<cluster>/cloud-passport/*-creds.yml`.

Before:

```yaml
dbaas:
  type: usernamePassword
  data:
    username: <username>
    password: <password>
```

After (secret already in the store - omit `create`):

```yaml
dbaas:
  type: external
  secretStore: default_store
  remoteRefPath: <cluster>
  properties:
    - name: username
    - name: password
```

After (new generated value is acceptable):

```yaml
cloud-deploy-sa-token:
  type: external
  create: true
  secretStore: default_store
  remoteRefPath: <cluster>
```

Rules:

- remove `data`
- `properties` entries must be objects: `- name: username`, not bare strings
- do not append `credId` to `remoteRefPath` - EnvGene appends it automatically
- for Azure, AWS, or GCP, keep `credId` to at most 32 characters
- omit `create` when the secret already exists
- set `create: true` only when a generated value is acceptable
- do not change built-in fields that store only a `credId` string

### Update the Cloud Passport main file

Open the matching main file (for example `environments/<cluster>/cloud-passport/cluster.yml`).

Replace every local Credential macro with `$type: credRef`. Search for:

```text
${creds.get('<credId>').username|password|secret}
${envgen.creds.get('<credId>').username|password|secret}
${cmdb.creds.get('<credId>').username|password|secret}
#creds{LOGIN_PARAM, PASSWORD_PARAM}
#credscl{LOGIN_PARAM, PASSWORD_PARAM}
#credsns{LOGIN_PARAM, PASSWORD_PARAM}
```

Before:

```yaml
dbaas:
  DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME: ${creds.get("dbaas").username}
  DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD: ${creds.get("dbaas").password}
consul:
  CONSUL_ADMIN_TOKEN: ${creds.get("consul").secret}
```

After:

```yaml
dbaas:
  DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME:
    $type: credRef
    credId: dbaas
    property: username
  DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD:
    $type: credRef
    credId: dbaas
    property: password
consul:
  CONSUL_ADMIN_TOKEN:
    $type: credRef
    credId: consul
```

### Legacy `#creds` / `#credscl` / `#credsns` keys

These macros sit in the parameter key. The value is the `credId`. Split each key into two
parameters with `$type: credRef`.

Before:

```yaml
'#creds{TEST_CREDS_LOGIN, TEST_CREDS_PASSWORD}': test-cred
```

After:

```yaml
TEST_CREDS_LOGIN:
  $type: credRef
  credId: test-cred
  property: username
TEST_CREDS_PASSWORD:
  $type: credRef
  credId: test-cred
  property: password
```

All three variants expand the same way.

Do not add `$type: credRef` to `technicalConfigurationParameters`.

Do not edit generated files under `effective-set/` by hand.

**Result:** Cloud Passport Credentials and main files use External Credentials and Credential
References.

## Step 4. Convert Shared Credentials

Open each file listed in `envTemplate.sharedMasterCredentialFiles` across all `env_definition.yml`
files, and also any unbound Shared Credential files.

Apply the same rules as Step 3 for Credential YAML.

Before:

```yaml
ID_TOCP_CLIENT_CREDS:
  type: usernamePassword
  data:
    username: <username>
    password: <password>
```

After:

```yaml
ID_TOCP_CLIENT_CREDS:
  type: external
  secretStore: default_store
  remoteRefPath: <cluster>/shared
  properties:
    - name: username
    - name: password
```

> [!IMPORTANT]
> `sharedMasterCredentialFiles` references the file by name **without** the `.yml` extension.
> EnvGene appends `.yml` automatically. If `env_definition.yml` has
> `"shared-credentials.yml"`, change it to `shared-credentials`. Including the extension causes
> the file to be skipped.

**Result:** Shared Credentials are External Credentials and `env_definition.yml` references are
updated where needed.

## Step 5. Convert System Credentials

System Credentials cover Git tokens, registry authentication, and deployer credentials. They live in:

- `/configuration/credentials/credentials.yml` - `self_token`, `cp_discovery` token, registry
- `environments/<cluster>/app-deployer/deployer-creds.yml` - deployer username and token

Apply the same conversion rules as Step 3 for Credential YAML, with these additional constraints:

- omit `create` - `create: true` is not allowed for System Credentials
- only Vault and GCP are supported as Secret Stores for System Credentials
- the secret must already exist in the Secret Store (from the prerequisite transfer)

After converting the Credential entries, update references in the configuration files.

`/configuration/deployer.yml` - before:

```yaml
cloud-deployer:
  username: "${envgen.creds.get('cloud-deployer-username').secret}"
  token: "${envgen.creds.get('cloud-deployer-token').secret}"
```

After:

```yaml
cloud-deployer:
  username:
    $type: credRef
    credId: cloud-deployer-username
  token:
    $type: credRef
    credId: cloud-deployer-token
```

`/configuration/integration.yml` - before:

```yaml
self_token: "${envgen.creds.get('self-token-cred').secret}"
cp_discovery:
  gitlab:
    token: "${envgen.creds.get('cp-discovery-repository-cred').secret}"
```

After:

```yaml
self_token:
  $type: credRef
  credId: self-token-cred
cp_discovery:
  gitlab:
    token:
      $type: credRef
      credId: cp-discovery-repository-cred
```

`credentialsId` fields in Artifact Definition and Registry Definition files stay as plain strings.

See [EnvGene System Credentials](/docs/features/external-creds.md#envgene-system-credentials).

**Result:** System Credentials converted to External Credentials.

## Step 6. Update environment-specific parameters

Replace the same macros as in Step 3 (`creds.get`, `envgen.creds.get`, `cmdb.creds.get`, `#creds`,
`#credscl`, `#credsns`) with `$type: credRef` in:

- environment-specific `deployParameters` and `e2eParameters`
- ParameterSets under `environments/<cluster>/<env>/Inventory/parameters/`,
  `environments/<cluster>/parameters/`, and `environments/parameters/`

Use the same before/after shapes as in Step 3.

Do not add `$type: credRef` to `technicalConfigurationParameters`. Do not edit `effective-set/`
files by hand.

**Result:** environment-specific parameters use Credential References.

## Step 7. Remove stale generated Credentials files

Each Environment Instance has a generated file at:

```text
environments/<cluster>/<env>/Credentials/credentials.yml
```

This file was produced by a previous pipeline run from the old Template. It contains local
`type: usernamePassword` or `type: secret` entries and causes the pipeline to fail with
`Only external credentials allowed` if it remains.

Delete every such file for all Environment Instances you are migrating.

The pipeline regenerates this file from the new Template (only `type: external` entries).

**Result:** stale generated Credentials files removed.

## Step 8. Validate before the pipeline

Check:

- all changed YAML files are syntactically valid
- every Environment Instance, when its sources are merged, produces External Credentials only
- no Credential file has a leftover `data` block for converted entries
- `credRef.property` matches a name in the Credential's `properties` list
- every `secretStore` ID exists in `/configuration/secret-stores.yml`
- no `$type: credRef` in `technicalConfigurationParameters`
- secrets exist in the store for all entries where `create` is omitted
- `sharedMasterCredentialFiles` entries do not have the `.yml` extension

**Result:** Instance Repository ready for the Instance pipeline.

## Step 9. Run the Instance pipeline

Start with a non-production Environment Instance.

```text
ENV_NAMES=<environment-name>
ENV_TEMPLATE_VERSION=<artifactId>:<version>
ENV_BUILDER=true
GENERATE_EFFECTIVE_SET=true
CMDB_IMPORT=false
```

Keep any other No-CMDB pipeline parameters from your working flow unchanged. See
[Update template version](/docs/how-to/update-template-version.md) if you set the Template version
manually in `env_definition.yml`.

The pipeline generates the Environment Instance, builds the External Credential Context,
prepares external secrets according to `create`, and generates the Effective Set.

Do not run a test deployment if generation fails.

**Result:** Environment Instance generated with External Credentials.

## Step 10. Verify the generated result

For each Environment Instance you ran, check:

- `environments/<cluster>/<env>/Credentials/credentials.yml` - all entries are `type: external`
- `effective-set/external-credential/external-credentials.yaml` - expected Credentials listed
- `effective-set/deployment/` - deployment contexts use VALS or ESO references, not plaintext

If verification fails, fix the configuration and re-run Step 9 for those environments.

**Result:** generated External Credentials validated.

## Step 11. Run a test deployment

Run a test deployment for the same environments. Confirm that applications start and that
authentication to dependent services works.

When generation and the test deployment succeed, continue with the remaining Environment Instances
the same way.

**Result:** External Credentials validated end-to-end.

## Rollback

### Before keeping the new Template version

1. keep using the previous Template version
2. revert Instance Repository changes
3. re-run the Instance pipeline on the test environments

### After keeping the new Template version

1. restore the previous Template version
2. restore consistent Instance Repository changes
3. regenerate Environment Instances and Effective Sets
4. do not delete external secrets until confirmed unused

## See also

- [Migrate Template Repository to External Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md)
- [UC-MIG-1 Migration CLI](/docs/analysis/external-credentials-migration-cli.md)
- [External Credentials Management](/docs/features/external-creds.md)
- [Update template version](/docs/how-to/update-template-version.md)
- [Generate Effective Set](/docs/how-to/generate-effective-set.md)
- [EnvGene pipelines](/docs/envgene-pipelines.md)
- [External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md)
- [Sample External Credentials](/docs/samples/external-credentials/)
