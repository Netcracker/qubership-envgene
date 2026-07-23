# Migrate Instance Repository to External Credentials

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Step 1. Define migration scope](#step-1-define-migration-scope)
- [Step 2. Configure Secret Store](#step-2-configure-secret-store)
- [Step 3. Update Shared Credentials](#step-3-update-shared-credentials)
- [Step 4. Update Cloud Passport Credentials](#step-4-update-cloud-passport-credentials)
- [Step 5. Update System Credentials](#step-5-update-system-credentials)
- [Step 6. Validate changes](#step-6-validate-changes)
- [Step 7. Run TEMPORARY smoke](#step-7-run-temporary-smoke)
- [Step 8. Verify the result](#step-8-verify-the-result)
- [Step 9. Run test deployment](#step-9-run-test-deployment)
- [Step 10. Run PERSISTENT cutover](#step-10-run-persistent-cutover)
- [Step 11. Roll out](#step-11-roll-out)
- [Rollback](#rollback)
- [Common mistakes](#common-mistakes)
- [See also](#see-also)

## Description

Update the Instance Repository to move an Environment Instance from local Credentials to External
Credentials.

In the Instance Repository:

1. identify Environment Instances that migrate together
2. configure the Secret Store
3. convert Shared Credentials to `type: external`
4. convert Cloud Passport Credentials to `type: external`
5. decide how to handle System Credentials
6. validate the new Template version in `TEMPORARY` mode
7. run a test deployment
8. pin the Template version in `PERSISTENT` mode

Credential Template and `$type: credRef` changes belong in the Template Repository.

EnvGene builds the final Credential File from Shared Credentials, then Cloud Passport Credentials,
then Credential Template. If one `credId` is defined in multiple sources, the higher-priority
definition wins.

The final Credential File for one Environment Instance must contain either local Credentials only,
or External Credentials only. Mixing `type: external` with `type: usernamePassword` or `type: secret`
is not supported.

System Credentials are handled separately and are not part of the Environment Instance final
Credential File.

Moving Credential values into the external Secret Store is a separate process. Do not add secret
values to Git, Merge Requests, or migration notes.

> [!WARNING]
> External Credentials migration for BG deployment cases is out of scope.

## Prerequisites

Before you start, confirm that:

- EnvGene is upgraded to `<version>`
- the Instance pipeline is available
- an external Secret Store is available
- CI/CD variables for Secret Store access are configured
- Credential value preparation in the external Secret Store is a separate process
- CMDB import is disabled for the Environment Instances you migrate

Know the concrete Environment Template version with External Credentials support before
`TEMPORARY smoke`.

CMDB import is not supported for Environment Instances with External Credentials.

## Step 1. Define migration scope

Find all Environment Instances:

```text
environments/<cluster>/<env>/Inventory/env_definition.yml
```

For each Environment Instance, check:

```yaml
envTemplate:
  name: <template-name>
  artifact: <current-version>
```

Also check `inventory.cloudPassport` and `envTemplate.sharedMasterCredentialFiles`.

Identify non-prod and prod Environment Instances. If the type is ambiguous, confirm it with the
project owner.

Select the first non-prod Environment Instance.

Find all Environment Instances that use the same Cloud Passport or Shared Credential file.

If several Environment Instances share a Cloud Passport or Shared Credential file:

- migrate the related Environment Instances together
- or split the shared Credential file first

Check unbound Shared Credentials and Cloud Passports. If a file or Cloud Passport exists but is not
referenced in any `env_definition.yml`, decide whether to include it. Do not add bindings
automatically.

**Result:** First non-prod Environment Instance selected. Related Environment Instances and
Credential files identified.

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
  projectId: "468649328578"
```

### AWS Secrets Manager

```yaml
default_store:
  type: aws
  region: eu-west-1
```

### Azure Key Vault

```yaml
default_store:
  type: azure
  vaultName: project-vault
```

The Secret Store identifier must match `[A-Za-z_][A-Za-z0-9_]*`.

Configure CI/CD variables for authentication according to the
[External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md).

Do not store tokens or keys in Git.

**Result:** Secret Store defined in the Instance Repository. CI/CD variables configured.

## Step 3. Update Shared Credentials

Open Shared Credential files bound to the selected Environment Instance group. Convert local
Credentials to `type: external`.

### Multi-field Credential

Before migration:

```yaml
shared-integration-cred:
  type: usernamePassword
  data:
    username: ENC[...]
    password: ENC[...]
```

After migration:

```yaml
shared-integration-cred:
  type: external
  secretStore: default_store
  remoteRefPath: shared/integration
  properties:
    - name: username
    - name: password
```

### Single-value Credential

Before migration:

```yaml
shared-token:
  type: secret
  data:
    secret: ENC[...]
```

After migration:

```yaml
shared-token:
  type: external
  secretStore: default_store
  remoteRefPath: shared/token
```

For each Credential: remove `data`, set `type: external`, set `secretStore` and `remoteRefPath`,
add `properties` only for multi-field Credentials, and do not set `create` for an existing
Credential.

Do not append `credId` to `remoteRefPath`. EnvGene appends it when building `normalizedSecretName`.

**Result:** Bound Shared Credentials converted to `type: external`.

## Step 4. Update Cloud Passport Credentials

Open the Cloud Passport credentials file bound to the selected group. Convert local Credentials the
same way as Shared Credentials.

```yaml
cloud-deploy-cred:
  type: external
  secretStore: default_store
  remoteRefPath: cluster
```

```yaml
dbaas-cluster-dba-cred:
  type: external
  secretStore: default_store
  remoteRefPath: cluster
  properties:
    - name: username
    - name: password
```

Do not append `credId` to `remoteRefPath`.

Built-in references stay string values:

```yaml
defaultCredentialsId: cloud-deploy-cred
```

```yaml
credentialsId: cloud-deploy-cred
```

**Result:** Bound Cloud Passport Credentials converted to `type: external`.

## Step 5. Update System Credentials

Check System Credentials under `/configuration/credentials/` and
`environments/<cluster>/app-deployer/*-creds.yml`.

For each shared Credential file, identify all Environment Instances that use it.

Choose whether to migrate System Credentials in this phase or separately.

System Credentials can remain local. They are not part of the Environment Instance Credential File,
so they do not affect the local-or-external mixing rule.

External System Credentials support only Vault or GCP Secret Stores. AWS Secrets Manager and Azure
Key Vault are not supported for System Credentials. See
[EnvGene System Credentials](/docs/features/external-creds.md#envgene-system-credentials).

If you migrate `app-deployer` Credentials in this phase, update them before the test deployment.

```yaml
system-cred:
  type: external
  secretStore: default_store
  remoteRefPath: system
  properties:
    - name: username
    - name: password
```

Omit `properties` for single-value Credentials. Remove `data`. Do not set `create` for an existing
Credential. Always set an explicit `remoteRefPath`.

**Result:** Decision made for System Credentials. Migration completed if required.

## Step 6. Validate changes

Before `TEMPORARY smoke`, confirm:

- YAML files are valid
- `/configuration/secret-stores.yml` contains every `secretStore` in use
- Shared and Cloud Passport Credentials have no `data`
- multi-field Credentials have `username` and `password`
- single-value Credentials omit `properties`
- `remoteRefPath` does not end with a redundantly appended `credId`
- related Environment Instances are accounted for
- the concrete Template version is confirmed
- CMDB import is disabled
- all active sources for the selected Environment Instance are External Credentials (Credential
  Template, Cloud Passport, Shared Credentials)

Check matching `credId` values across Credential Template, Cloud Passport Credentials, and Shared
Credentials. Confirm the expected source matches merge priority (Shared, then Cloud Passport, then
Credential Template). Structure must match across definitions in use.

Validate System Credentials separately.

**Result:** Instance Repository ready for `TEMPORARY smoke`.

## Step 7. Run TEMPORARY smoke

Run the Instance pipeline manually for the selected non-prod Environment Instance:

```text
ENV_TEMPLATE_VERSION=<artifactId>:<concrete-version>
ENV_TEMPLATE_VERSION_UPDATE_MODE=TEMPORARY
ENV_NAMES=<cluster>/<environment>
ENV_BUILDER=true
GENERATE_EFFECTIVE_SET=true
CMDB_IMPORT=false
```

`TEMPORARY` does not pin the new Template version in `env_definition.yml`.

**Result:** Environment Instance and Effective Set generated with the new Template version without a
permanent switch.

## Step 8. Verify the result

### Environment Credential File

Check `environments/<cluster>/<env>/Credentials/credentials.yml`.

The file must list the full Credential set for the Environment Instance. Every entry must have
`type: external`. The file must not contain `type: usernamePassword`, `type: secret`, or `data`.

### External Credential Context

Check
`environments/<cluster>/<env>/effective-set/external-credential/external-credentials.yaml`.

The file must contain one entry per External Credential:

```yaml
credentials:
  app-db-cred:
    vals: "ref+vault://secret/cluster/env/database/app-db-cred"
    strategy: fail_if_absent
```

### Effective Set contexts

If a deployment context was generated, check External Credential references in
`effective-set/deployment/<namespace>/<application>/values/credentials.yaml`.

If you use `e2eParameters`, check `effective-set/pipeline/credentials.yaml`.

If you use supported built-in references, check `effective-set/topology/credentials.yaml`.

For `SECRET_FLOW=external-values`, the application must have `eso_support: true`.

If you do not use a Solution Descriptor, check only the generated pipeline contexts.

Confirm that all `credId` values resolve, all `secretStore` values exist, the final Credential File
is External-only, External Credential Context and Effective Set references are present, plaintext
secret values are absent, and the pipeline succeeded.

If validation fails, do not run the test deployment or `PERSISTENT cutover`.

**Result:** External Credentials validated in the generated Environment Instance and Effective Set.

## Step 9. Run test deployment

Run a test deployment manually on the selected non-prod Environment Instance.

If the deployment fails:

1. do not run `PERSISTENT cutover`
2. check External Credential references in the Effective Set
3. pass missing-value errors to the team that prepares External Credentials
4. fix the configuration
5. repeat `TEMPORARY smoke` and the test deployment

**Result:** Test deployment successfully uses External Credentials.

## Step 10. Run PERSISTENT cutover

After a successful test deployment, run the Instance pipeline manually:

```text
ENV_TEMPLATE_VERSION=<artifactId>:<concrete-version>
ENV_TEMPLATE_VERSION_UPDATE_MODE=PERSISTENT
ENV_NAMES=<cluster>/<environment>
ENV_BUILDER=true
GENERATE_EFFECTIVE_SET=true
CMDB_IMPORT=false
```

Check `environments/<cluster>/<env>/Inventory/env_definition.yml`. The `envTemplate.artifact` field
must contain the new concrete version:

```yaml
envTemplate:
  artifact: <artifactId>:<concrete-version>
```

**Result:** Environment Instance permanently switched to the new Environment Template version.

## Step 11. Roll out

Roll out in this order: first non-prod Environment Instance, remaining non-prod, then prod.

For each group:

1. check Shared Credentials and Cloud Passport Credentials used by the group
2. run `TEMPORARY smoke`
3. check the Environment Credential File and Effective Set
4. run the test deployment
5. run `PERSISTENT cutover`

**Result:** Selected Environment Instances converted to External Credentials.

## Rollback

### Before PERSISTENT cutover

1. fix Instance Repository changes
2. repeat `TEMPORARY smoke` and the test deployment
3. keep using the current Environment Template version

### After PERSISTENT cutover

1. restore previous Shared Credentials, Cloud Passport Credentials, and System Credentials if needed
2. restore the previous concrete Environment Template version
3. regenerate the Environment Instance and Effective Set
4. deploy the restored configuration

Rolling back Instance Repository configuration does not remove changes in the external Secret Store.

## Common mistakes

| Mistake                               | Fix                                                                |
|---------------------------------------|--------------------------------------------------------------------|
| `credId` not found                    | Check Credential Template, Cloud Passport, and Shared Credentials  |
| Local and external Credentials mixed  | Convert remaining active Credentials                               |
| One `credId` has different structures | Identify the correct source and structure                          |
| Secret Store not found                | Add it to `secret-stores.yml`                                      |
| External secret missing               | Contact the team that prepares External Credentials                |
| Test deployment failed                | Do not run `PERSISTENT cutover`; check External Credential refs    |
| ESO not supported                     | Use VALS or update the application                                 |
| CMDB import enabled                   | Set `CMDB_IMPORT=false`                                            |
| System Credential on AWS or Azure     | Use Vault or GCP for System Credentials                            |

## See also

- [Migrate Template Repository to External Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md)
- [External Credentials Management](/docs/features/external-creds.md)
- [Update template version](/docs/how-to/update-template-version.md)
- [Generate Effective Set](/docs/how-to/generate-effective-set.md)
- [EnvGene pipelines](/docs/envgene-pipelines.md)
- [External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md)
- [Sample External Credentials](/docs/samples/external-credentials/)
