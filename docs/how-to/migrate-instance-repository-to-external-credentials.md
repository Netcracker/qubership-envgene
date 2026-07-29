# Migrate Instance Repository to External Credentials

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Step 1. Inventory the Instance Repository](#step-1-inventory-the-instance-repository)
- [Step 2. Configure Secret Store](#step-2-configure-secret-store)
- [Step 3. Convert Cloud Passport Credentials](#step-3-convert-cloud-passport-credentials)
- [Step 4. Update Cloud Passport main files](#step-4-update-cloud-passport-main-files)
- [Step 5. Convert Shared Credentials](#step-5-convert-shared-credentials)
- [Step 6. Update environment-specific parameters](#step-6-update-environment-specific-parameters)
- [Step 7. Set SECRET_FLOW and Application SBOM ESO support](#step-7-set-secret_flow-and-application-sbom-eso-support)
- [Step 8. Convert EnvGene System Credentials](#step-8-convert-envgene-system-credentials)
- [Step 9. Validate before the pipeline](#step-9-validate-before-the-pipeline)
- [Step 10. Run TEMPORARY smoke](#step-10-run-temporary-smoke)
- [Step 11. Verify the generated result](#step-11-verify-the-generated-result)
- [Step 12. Run PERSISTENT cutover](#step-12-run-persistent-cutover)
- [Rollback](#rollback)
- [Common mistakes](#common-mistakes)
- [See also](#see-also)

## Description

Migrate the Instance Repository from local Credentials to External Credentials.

Finish
[Migrate Template Repository to External Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md)
and publish a concrete Template version first.

Then, for the Instance Repository:

1. inventory all Environment Instances and bound Credential sources
2. configure the Secret Store
3. convert Cloud Passport Credentials, then update Cloud Passport main files
4. convert Shared Credentials
5. replace local macros with `$type: credRef` in environment-specific parameters
6. set `SECRET_FLOW` and Application SBOM `eso_support` when you use ESO
7. convert System Credentials to External Credentials
8. run `TEMPORARY` smoke, verify, then `PERSISTENT`

### Instance rules

- After merge, each Environment Instance must use only External Credentials. Mixing
  `type: external` with `type: usernamePassword` or `type: secret` in one Environment Instance is
  not supported.
- Environment Instance Credentials come from Credential Template, Cloud Passport Credentials, and
  Shared Credentials. On duplicate `credId`, precedence is lowest to highest: Credential Template,
  then Cloud Passport, then Shared Credentials.
- `$type: credRef` works only in `deployParameters`, `e2eParameters`, and ParameterSets that feed
  those blocks. It does not work in `technicalConfigurationParameters`.
- Built-in fields stay plain `credId` strings.
- CMDB import is not supported for Environment Instances with External Credentials.
- BG deployment is out of scope.

Do not put secret values in Git, Merge Requests, or migration notes. Move existing values into the
external Secret Store by a separate secure process when you must keep them.

## Prerequisites

Before you start, confirm that:

- the Instance Repository already uses the No-CMDB approach
- EnvGene is upgraded to a version that includes External Credentials
- a concrete Template version with `external_credential_template` is published
- the Secret Store identifier is known, for example `default_store`
- CI/CD variables for Secret Store authentication are configured
- for each Credential you know whether the secret already exists, or a new generated value is
  acceptable (`create: true`)

## Step 1. Inventory the Instance Repository

Find all Environment Instances:

```text
environments/<cluster>/<env>/Inventory/env_definition.yml
```

For each Environment Instance, note:

- `inventory.cloudPassport`
- `envTemplate.sharedMasterCredentialFiles`
- environment-specific ParameterSets
- used `credId` values

Also list Cloud Passport credential files, Cloud Passport main files, Shared Credentials files, and
System Credential files under `/configuration/credentials/` and
`environments/<cluster>/app-deployer/*-creds.yml`.

Also migrate unbound Shared Credentials and Cloud Passports: files that exist but are not
referenced from any `env_definition.yml`. Convert them the same way as bound sources.

Migrate the whole Instance Repository. Shared Credential and Cloud Passport files apply to every
Environment Instance that binds them, so convert those sources completely.

**Result:** full inventory of Environment Instances and Credential sources.

## Step 2. Configure Secret Store

Create or update `/configuration/secret-stores.yml`.

### Vault

```yaml
default_store:
  type: vault
  mountPath: secret
```

### GCP Secret Manager

```yaml
default_store:
  type: gcp
  projectId: <project-id>
```

### AWS Secrets Manager

```yaml
default_store:
  type: aws
  region: <region>
```

### Azure Key Vault

```yaml
default_store:
  type: azure
  vaultName: <vault-name>
```

The Secret Store identifier must match `[A-Za-z_][A-Za-z0-9_]*`.

Configure CI/CD variables for authentication. For a non-default store, use variables with the
`<store_id>_` prefix. See
[External Credentials Management](/docs/features/external-creds.md) and the
[External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md).

Do not store tokens or keys in Git.

**Result:** Secret Store defined.

## Step 3. Convert Cloud Passport Credentials

Open each Cloud Passport credentials file. Convert local Credentials to `type: external`.

Before:

```yaml
dbaas-cluster-dba-cred:
  type: usernamePassword
  data:
    username: <current-username>
    password: <current-password>
```

After:

```yaml
dbaas-cluster-dba-cred:
  type: external
  create: true
  secretStore: default_store
  remoteRefPath: cluster
  properties:
    - name: username
    - name: password
```

Single-value example:

```yaml
cloud-deploy-cred:
  type: external
  create: true
  secretStore: default_store
  remoteRefPath: cluster
```

Rules:

- remove `data`
- multi-field `properties` use `- name: username` and `- name: password` objects, never bare strings
- do not append `credId` to `remoteRefPath` - EnvGene adds it when building the final secret name
- for Azure, AWS, and GCP, keep `credId` to at most 32 characters (see
  [Normalization to normalizedSecretName](/docs/features/external-creds.md#normalization-to-normalizedsecretname))
- always set an explicit `remoteRefPath` in Cloud Passport, Shared, and System Credential files
- omit `create` when the secret already exists
- set `create: true` when a new generated secret value is acceptable

Do not change Built-in string fields that only store a `credId`.

**Result:** Cloud Passport Credentials are External Credentials.

## Step 4. Update Cloud Passport main files

For each Cloud Passport you converted in Step 3, open the matching main file (for example
`cluster.yml`), not only `*-creds.yml`.

Replace `${creds.get(...)}`, `${envgen.creds.get(...)}`, and `${cmdb.creds.get(...)}` with
`$type: credRef`.

Before:

```yaml
dbaas:
  DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME: ${creds.get("dbaas-cluster-dba-cred").username}
  DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD: ${creds.get("dbaas-cluster-dba-cred").password}
```

After:

```yaml
dbaas:
  DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME:
    $type: credRef
    credId: dbaas-cluster-dba-cred
    property: username
  DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD:
    $type: credRef
    credId: dbaas-cluster-dba-cred
    property: password
```

Do not add `$type: credRef` to `technicalConfigurationParameters`.

Do not edit generated files under `effective-set/` by hand.

Finish credentials and the main file for one Cloud Passport before you move to the next.

**Result:** Cloud Passport main files use Credential References.

## Step 5. Convert Shared Credentials

Convert Shared Credentials files with the same rules as Cloud Passport Credentials.

Before:

```yaml
shared-app-cred:
  type: usernamePassword
  data:
    username: <current-username>
    password: <current-password>
```

After:

```yaml
shared-app-cred:
  type: external
  secretStore: default_store
  remoteRefPath: shared/integration
  properties:
    - name: username
    - name: password
```

Shared Credentials override Cloud Passport and Credential Template when `credId` values collide.

**Result:** Shared Credentials are External Credentials.

## Step 6. Update environment-specific parameters

Replace `${creds.get(...)}`, `${envgen.creds.get(...)}`, and `${cmdb.creds.get(...)}` with
`$type: credRef` in:

- environment-specific `deployParameters` and `e2eParameters`
- environment-specific ParameterSets under
  `environments/<cluster>/<env>/Inventory/parameters/`, `environments/<cluster>/parameters/`, and
  `environments/parameters/`

Use the same before/after shape as in Step 4.

Do not add `$type: credRef` to `technicalConfigurationParameters`.

Do not edit generated files under `effective-set/` by hand.

**Result:** supported environment-specific parameters use Credential References.

## Step 7. Set SECRET_FLOW and Application SBOM ESO support

`SECRET_FLOW` selects how sensitive parameters are emitted in the Effective Set. EnvGene discovers it
from the Cloud Passport. The attribute may also be set at Cloud, Namespace, or Application scope
(see [`SECRET_FLOW`](/docs/features/external-creds.md#secret_flow-attribute)).

| `SECRET_FLOW`     | Effective Set shape |
|-------------------|---------------------|
| `helm-values`     | VALS references     |
| `external-values` | ESO references      |

Sample Cloud Passport uses VALS:

```yaml
global:
  SECRET_FLOW: helm-values
```

If the effective `SECRET_FLOW` for an application is `external-values`, that application must declare
`eso_support: true` in its Application SBOM. Otherwise Effective Set generation fails.

Check every place that sets `SECRET_FLOW`, and check Application SBOM / appdefs for applications that
use `external-values`. See also
[eso_support](/docs/features/external-creds.md#eso_support-attribute).

**Result:** `SECRET_FLOW` and `eso_support` are consistent for every application.

## Step 8. Convert EnvGene System Credentials

Convert System Credentials used by EnvGene for Git, registry, and deployer operations.

Cover these parameters and their Credential entries:

| Parameter                         | Typical location                                              |
|-----------------------------------|---------------------------------------------------------------|
| `self_token`                      | `/configuration/integration.yml`                              |
| `cp_discovery.gitlab.token`       | `/configuration/integration.yml`                              |
| registry username/password        | `/configuration/registry.yml`                                 |
| deployer username/token           | `deployer.yml` and optional `deployer-creds.yml` nearby       |
| Artifact Definition `credentialsId` | `/configuration/artifact_definitions/`                     |
| Registry Definition `credentialsId`  | registry definition files                                  |

Credential entries live in `/configuration/credentials/credentials.yml`, except deployer Credentials
that may live in `deployer-creds.yml` next to `deployer.yml`.

For integration, registry, and deployer parameters, replace local macros with `$type: credRef`.
Artifact Definition and Registry Definition `credentialsId` stay plain strings.

Before:

```yaml
# /configuration/integration.yml
self_token: "${envgen.creds.get('self-token-cred').secret}"
```

```yaml
# /configuration/credentials/credentials.yml
self-token-cred:
  type: secret
  data:
    secret: <token>
```

After:

```yaml
# /configuration/integration.yml
self_token:
  $type: credRef
  credId: self-token-cred
```

```yaml
# /configuration/credentials/credentials.yml
self-token-cred:
  type: external
  secretStore: default_store
  remoteRefPath: /vcs/envgene-bot
```

Artifact Definition and Registry Definition example:

```yaml
credentialsId: artifactory-cred
```

System Credential rules from the feature specification:

- omit `create` - `create: true` is not allowed for System Credentials
- the secret must already exist in the Secret Store
- only Vault and GCP are supported as Secret Stores for System Credentials
- System Credentials are not part of the Environment Instance single-category rule
- some parameters may still be supplied by CI/CD variables instead of a Credential

See [EnvGene System Credentials](/docs/features/external-creds.md#envgene-system-credentials).

**Result:** System Credentials converted to External Credentials.

## Step 9. Validate before the pipeline

Confirm that:

- changed YAML files are valid
- every Environment Instance merges to External Credentials only
- Shared, Cloud Passport, and System Credential files have no leftover `data` for migrated entries
- `credRef.property` matches Credential `properties`
- every `secretStore` exists in `secret-stores.yml`
- technical configuration has no `$type: credRef`
- secrets already exist when `create` is omitted
- for `SECRET_FLOW: external-values`, applications have `eso_support: true`

If a previously generated `Credentials/credentials.yml` still contains local entries, move any
values you still need to the Secret Store first. Deleting that stale generated file and regenerating
it is only a workaround, not a standard step.

**Result:** Instance Repository ready for `TEMPORARY` smoke.

## Step 10. Run TEMPORARY smoke

Run the Instance pipeline with the new Template version:

```text
ENV_NAMES=<environment-name-or-list>
ENV_TEMPLATE_VERSION=<artifactId>:<version>
ENV_TEMPLATE_VERSION_UPDATE_MODE=TEMPORARY
ENV_BUILDER=true
GENERATE_EFFECTIVE_SET=true
CMDB_IMPORT=false
```

Keep any other No-CMDB pipeline parameters from your working flow unchanged.

The pipeline must generate the Environment Instance, build the External Credential Context, prepare
external secrets according to `create`, and generate the Effective Set.

Do not move to `PERSISTENT` if the pipeline fails.

**Result:** Environment Instances generated without pinning the Template version.

## Step 11. Verify the generated result

For each Environment Instance, check:

- `environments/<cluster>/<env>/Credentials/credentials.yml` contains only `type: external`
- `effective-set/external-credential/external-credentials.yaml` lists the expected Credentials
- deployment contexts under `effective-set/deployment/` use VALS or ESO references, not plaintext
- `effective-set/pipeline/credentials.yaml` when you use `e2eParameters`
- `effective-set/topology/credentials.yaml` when you use supported Built-in references
- for `SECRET_FLOW: external-values`, ESO references are present and applications have
  `eso_support: true`

If verification fails, fix the configuration and repeat `TEMPORARY` smoke. Run a test deployment
after a successful smoke when you need that extra check.

**Result:** generated External Credentials validated.

## Step 12. Run PERSISTENT cutover

After successful smoke and verification, run:

```text
ENV_NAMES=<environment-name-or-list>
ENV_TEMPLATE_VERSION=<artifactId>:<version>
ENV_TEMPLATE_VERSION_UPDATE_MODE=PERSISTENT
ENV_BUILDER=true
GENERATE_EFFECTIVE_SET=true
CMDB_IMPORT=false
```

Confirm that `envTemplate.artifact` stores the new Template version and Effective Set generation
succeeds for the Environment Instances.

**Result:** Instance Repository permanently switched to External Credentials.

## Rollback

### Before PERSISTENT

1. keep using the previous Template version
2. fix Instance Repository changes
3. repeat `TEMPORARY` smoke

### After PERSISTENT

1. restore the previous Template version
2. restore consistent Instance Repository changes
3. regenerate Environment Instances and Effective Sets
4. do not delete external secrets until you confirm they are unused

## Common mistakes

| Error                               | What to check                                           |
|-------------------------------------|---------------------------------------------------------|
| Used `credId` is not declared       | Credential Template, Cloud Passport, Shared Credentials |
| Only external credentials allowed   | Merged sources and stale `Credentials/credentials.yml`  |
| Credential Reference not resolved   | `credId` spelling and merged Credential File            |
| Invalid Credential property         | `property` vs `properties`                              |
| `properties: [username, password]`  | Use `- name: username` / `- name: password`             |
| Secret Store not found              | `/configuration/secret-stores.yml`                      |
| Secret missing                      | Store path and whether `create` was omitted             |
| ESO capability validation failed    | `SECRET_FLOW: external-values` needs `eso_support: true`|
| `create: true` on System Credential | Omit `create`. Pre-create the secret                    |
| CMDB import failed                  | Use No-CMDB flow                                        |
| Macros left in Cloud Passport main  | Convert main file, not only `*-creds.yml`               |

## See also

- [Migrate Template Repository to External Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md)
- [External Credentials Management](/docs/features/external-creds.md)
- [Update template version](/docs/how-to/update-template-version.md)
- [Generate Effective Set](/docs/how-to/generate-effective-set.md)
- [EnvGene pipelines](/docs/envgene-pipelines.md)
- [External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md)
- [Sample External Credentials](/docs/samples/external-credentials/)
