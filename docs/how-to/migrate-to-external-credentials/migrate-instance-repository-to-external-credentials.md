# Migrate Instance Repository to External Credentials

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Step 1. Inventory the Instance Repository](#step-1-inventory-the-instance-repository)
- [Step 2. Decide create and remoteRefPath](#step-2-decide-create-and-remoterefpath)
- [Step 3. Configure Secret Store](#step-3-configure-secret-store)
- [Step 4. Convert Cloud Passport Credentials and main file](#step-4-convert-cloud-passport-credentials-and-main-file)
- [Step 5. Convert Shared Credentials](#step-5-convert-shared-credentials)
- [Step 6. Convert System Credentials](#step-6-convert-system-credentials)
- [Step 7. Update environment-specific parameters](#step-7-update-environment-specific-parameters)
- [Step 8. Remove stale generated Credentials files](#step-8-remove-stale-generated-credentials-files)
- [Step 9. Validate before the pipeline](#step-9-validate-before-the-pipeline)
- [Step 10. Run the Instance pipeline (first run - skip)](#step-10-run-the-instance-pipeline-first-run---skip)
- [Step 11. Transfer credential values and provision the Store](#step-11-transfer-credential-values-and-provision-the-store)
- [Step 12. Run the Instance pipeline again (apply)](#step-12-run-the-instance-pipeline-again-apply)
- [Step 13. Verify the generated result](#step-13-verify-the-generated-result)
- [Step 14. Run a test deployment](#step-14-run-a-test-deployment)
- [Rollback](#rollback)
- [See also](#see-also)

## Description

Migrate the Instance Repository from local Credentials to External Credentials.

Complete
[Migrate Template Repository to External Credentials](migrate-template-repository-to-external-credentials.md)
and publish a concrete Template version before starting here.

Do not remove `data` from any Credential YAML before its real value is already in the Secret
Store. After cutover, EnvGene no longer reads values from Git. If `create: true` is set and the
secret is missing, EnvGene generates a new value - the previous password, token, or key is lost.

Do not put secret values in Git, Merge Requests, or migration notes at any point.

### Credential value transfer

Moving real passwords and tokens into the Secret Store is a separate procedure from this YAML
cutover, and it runs in **two parts** at two different points:

| When | What | Covered by |
|------|------|------------|
| Before you remove `data:` in Steps 4-6 (below) | Collect values still committed in Instance Repository Git | [Transfer Credential Values, Step 2](transfer-credential-values-to-external-credentials.md#step-2-collect-from-the-instance-repository) |
| After [Step 10](#step-10-run-the-instance-pipeline-first-run---skip) produces an External Credential Context | Export Jenkins-sourced values, match them into Context, provision the Store | [Transfer Credential Values, Steps 3-5](transfer-credential-values-to-external-credentials.md#step-3-export-from-jenkins) |

Do not wait until the end of this how-to to start transferring values - by then the Git-sourced
ones are already gone. Run the "before" half while you convert Cloud Passport and Shared
Credentials (Steps 4-5), not after.

`migration-cli` does not cover System Credentials (`configuration/credentials/`,
`app-deployer/deployer-creds.yml`) - see [Step 6](#step-6-convert-system-credentials).

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
- `/configuration/secret-stores.yml` defines every Secret Store id you reference (Step 2)
- CI/CD authentication variables for those stores are configured
- for each Credential you know who creates the value (EnvGene, pre-existing, or provider) and the
  Store path prefix before you remove `data`
- `migration-cli` installed if any secret value you need still lives in Instance Repository Git or
  Jenkins CMDB - see [Transfer Credential Values to the Secret
  Store](transfer-credential-values-to-external-credentials.md#step-1-install-migration-cli)

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
| `/configuration/credentials/credentials.yml`          | System Credentials (git token, registry)              |
| `environments/<cluster>/<env>/Credentials/credentials.yml` | Generated files - do not edit. Delete in Step 8. |

For each local Credential (`type: usernamePassword` or `type: secret`), record:

- `credId`
- source file
- whether `data` contains a real value or a stub (`envgeneNullValue` / empty)

Include unbound files - Cloud Passport or Shared Credential files that exist but are not
referenced from any `env_definition.yml`. Convert them the same way.

**Result:** full inventory of Environment Instances, Credential sources, and per-`credId` values.

## Step 2. Decide create and remoteRefPath

For every local Credential from the inventory, decide in this order:

1. **Scope** - cluster (Cloud Passport), environment, shared across environments, system, or
   provider.
2. **Who creates the value** - EnvGene, pre-existing, or provider. If unclear, stop and confirm.
3. **`create`** - see the matrix.
4. **`remoteRefPath`** - prefix only. EnvGene appends the normalised `credId`.
5. **Confirm ambiguous cases** before you convert YAML or delete `data`.

### Decision matrix

| Who creates the value | Migration notes | Final Credential YAML |
|-----------------------|-----------------|------------------------|
| EnvGene may generate | `create: true` | `create: true` |
| Secret must already exist | `create: false` | omit `create` |
| External provider creates it | `create: false` | omit `create` |
| Unknown | do not convert yet | leave unchanged |

`create` is EnvGene runtime behaviour when the secret is absent. Separately, if you copy an
existing plaintext value from Git into the Secret Store during migration, that is a distinct
action - see [Credential value transfer](#credential-value-transfer) above. That transfer never
appears in the final Credential YAML.

### Default proposals by source (confirm before apply)

| Source | Typical path proposal | Typical create proposal |
|--------|-----------------------|-------------------------|
| Cloud Passport | `<cluster>` | omit (`false` in notes) |
| Environment-level Shared | `<cluster>/<environment>` | `true` if new values are OK |
| Cluster / repo Shared | `external` or approved shared path | omit |
| System Credentials | approved system path (fallback `external`) | always omit |

Do not set `create: true` for System Credentials or confirmed provider-managed Credentials.

Names such as `consul`, `dbaas`, or `service-account` in a `credId` are review signals only -
confirm ownership and path before converting.

**Result:** confirmed create and path decisions for every Credential you will convert.

## Step 3. Configure Secret Store

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

## Step 4. Convert Cloud Passport Credentials and main file

Work through one Cloud Passport at a time: convert its `*-creds.yml` and its main file together
before moving to the next.

> [!IMPORTANT]
> If any Credential you are about to convert has its real value only in Git (`data.username` /
> `data.password` / `data.secret` is a real value, not a stub), collect it with `migration-cli
> collect` **before** you remove `data` below - see [Transfer Credential Values, Step
> 2](transfer-credential-values-to-external-credentials.md#step-2-collect-from-the-instance-repository).
> Once `data` is gone, that value cannot be recovered from Git.

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

After (secret already in the store or provider-managed - omit `create`):

```yaml
dbaas:
  type: external
  secretStore: default_store
  remoteRefPath: <cluster>
  properties:
    - name: username
    - name: password
```

After (EnvGene generation of a new value is confirmed):

```yaml
cloud-deploy-sa-token:
  type: external
  create: true
  secretStore: default_store
  remoteRefPath: <cluster>
```

Rules:

- remove `data` only after the value is collected (see the callout above) or generation is
  confirmed
- `properties` entries must be objects: `- name: username`, not bare strings
- do not append `credId` to `remoteRefPath` - EnvGene appends it automatically
- for Azure, AWS, or GCP, keep `credId` to at most 32 characters
- omit `create` when the secret already exists or a provider creates it
- set `create: true` only when EnvGene generation is explicitly allowed
- default path proposal is `<cluster>` - confirm before apply
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

## Step 5. Convert Shared Credentials

Open each file listed in `envTemplate.sharedMasterCredentialFiles` across all `env_definition.yml`
files, and also any unbound Shared Credential files you chose to include.

> [!IMPORTANT]
> Same rule as Step 4: collect any Git-only real value with `migration-cli collect` before you
> remove its `data` block, if you have not already covered it in one `collect` run.

Apply the same conversion rules as Step 4 for Credential YAML, using the decisions from Step 2:

- cluster / repository Shared - typical path `external` (or an approved shared path), omit `create`
- environment-level Shared - typical path `<cluster>/<environment>`, `create: true` only when new
  values are allowed

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
  remoteRefPath: external
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

## Step 6. Convert System Credentials

System Credentials cover git tokens, registry authentication, and deployer credentials. They live in:

- `/configuration/credentials/credentials.yml` - `self_token`, `cp_discovery` token, registry
- `environments/<cluster>/app-deployer/deployer-creds.yml` - deployer username and token

Apply the same conversion rules as Step 4 for Credential YAML, with these additional constraints:

- omit `create` - `create: true` is not allowed for System Credentials
- only Vault and GCP are supported as Secret Stores for System Credentials
- the secret must already exist in the Secret Store
- use an approved system path (fallback `external`)

> [!IMPORTANT]
> `migration-cli collect` / `export-credentials` / `fill` explicitly treat
> `configuration/credentials/` as out of scope - they do not read or transfer System Credential
> values. Get these values into the Secret Store through another route (your Store's own
> tooling, or a manually authored `external-cred-provision` input file) before you remove `data`
> here. Confirm the exact procedure with the Platform team if it is not already established for
> your Store type.

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

## Step 7. Update environment-specific parameters

Replace the same macros as in Step 4 (`creds.get`, `envgen.creds.get`, `cmdb.creds.get`, `#creds`,
`#credscl`, `#credsns`) with `$type: credRef` in:

- environment-specific `deployParameters` and `e2eParameters`
- ParameterSets under `environments/<cluster>/<env>/Inventory/parameters/`,
  `environments/<cluster>/parameters/`, and `environments/parameters/`

Use the same before/after shapes as in Step 4.

Do not add `$type: credRef` to `technicalConfigurationParameters`. Do not edit `effective-set/`
files by hand.

**Result:** environment-specific parameters use Credential References.

## Step 8. Remove stale generated Credentials files

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

## Step 9. Validate before the pipeline

Check:

- all changed YAML files are syntactically valid
- every Environment Instance, when its sources are merged, produces External Credentials only
- no Credential file has a leftover `data` block for converted entries
- every converted Credential had a confirmed creation owner and path
- `credRef.property` matches a name in the Credential's `properties` list
- every `secretStore` id exists in `/configuration/secret-stores.yml`
- no `$type: credRef` in `technicalConfigurationParameters`
- Git-sourced real values you will need have already been collected (Steps 4-5 callouts)
- no `create: false` written in YAML (omit the field instead)
- `sharedMasterCredentialFiles` entries do not have the `.yml` extension

**Result:** Instance Repository ready for the Instance pipeline.

## Step 10. Run the Instance pipeline (first run - skip)

Start with a non-production Environment Instance.

```text
ENV_NAMES=<environment-name>
ENV_TEMPLATE_VERSION=<artifactId>:<version>
ENV_BUILDER=true
GENERATE_EFFECTIVE_SET=true
EXTERNAL_CREDENTIAL_PROVISIONING=skip
CMDB_IMPORT=false
```

Keep any other No-CMDB pipeline parameters from your working flow unchanged. See
[Update template version](/docs/how-to/update-template-version.md) if you set the Template version
manually in `env_definition.yml`.

`EXTERNAL_CREDENTIAL_PROVISIONING=skip` makes this run generate the Environment Instance, the
External Credential Context, and the Effective Set **without** calling `external-cred-provision` -
so it does not fail just because secret values are not in the Store yet.

Do not run a test deployment against this run's Effective Set - `credRef` entries do not resolve
to real values until after Step 11-12.

Do not run a test deployment if generation fails.

**Result:** Environment Instance generated; External Credential Context available for value
transfer.

## Step 11. Transfer credential values and provision the Store

Follow [Transfer Credential Values to the Secret Store](transfer-credential-values-to-external-credentials.md):

- Jenkins-sourced values (Cloud Passport / Shared Credentials that came from Jenkins CMDB):
  [Step 3, `export-credentials`](transfer-credential-values-to-external-credentials.md#step-3-export-from-jenkins)
- All values, using the collect output from Steps 4-5 and/or the export from above:
  [Step 4, `fill`](transfer-credential-values-to-external-credentials.md#step-4-fill-the-external-credential-context)
- [Step 5, `external-cred-provision`](transfer-credential-values-to-external-credentials.md#step-5-provision-into-the-secret-store)

For System Credential values, use the route you confirmed in [Step 6](#step-6-convert-system-credentials) -
`migration-cli` does not transfer those.

**Result:** all required secret values are in the Secret Store.

## Step 12. Run the Instance pipeline again (apply)

```text
ENV_NAMES=<environment-name>
ENV_TEMPLATE_VERSION=<artifactId>:<version>
GENERATE_EFFECTIVE_SET=true
EXTERNAL_CREDENTIAL_PROVISIONING=apply
CMDB_IMPORT=false
```

`apply` is the default - you can omit the parameter entirely instead of setting it explicitly.
Keep the other pipeline parameters from Step 10 unless your flow requires otherwise.

Do not run a test deployment if generation fails.

**Result:** Effective Set resolves `credRef` entries against real Secret Store values.

## Step 13. Verify the generated result

For each Environment Instance you ran, check:

- `environments/<cluster>/<env>/Credentials/credentials.yml` - all entries are `type: external`
- `effective-set/external-credential/external-credentials.yaml` - expected Credentials listed
- `effective-set/deployment/` - deployment contexts use VALS or ESO references, not plaintext

If verification fails, fix the configuration and re-run from [Step 10](#step-10-run-the-instance-pipeline-first-run---skip)
for those environments.

**Result:** generated External Credentials validated.

## Step 14. Run a test deployment

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

- [Migrate Template Repository to External Credentials](migrate-template-repository-to-external-credentials.md)
- [Transfer Credential Values to the Secret Store](transfer-credential-values-to-external-credentials.md)
- [UC-MIG-1 Migration CLI](/docs/analysis/external-credentials-migration-cli.md)
- [External Credentials Management](/docs/features/external-creds.md)
- [Update template version](/docs/how-to/update-template-version.md)
- [Generate Effective Set](/docs/how-to/generate-effective-set.md)
- [EnvGene pipelines](/docs/envgene-pipelines.md)
- [External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md)
- [Sample External Credentials](/docs/samples/external-credentials/)
