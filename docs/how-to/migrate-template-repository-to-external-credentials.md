# Migrate Template Repository to External Credentials

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Step 1. Analyse used Credentials](#step-1-analyse-used-credentials)
- [Step 2. Create Credential Template](#step-2-create-credential-template)
- [Step 3. Update Template Descriptor](#step-3-update-template-descriptor)
- [Step 4. Replace local Credential references](#step-4-replace-local-credential-references)
- [Step 5. Verify changes](#step-5-verify-changes)
- [Step 6. Publish new Template version](#step-6-publish-new-template-version)
- [Rollback](#rollback)
- [Common mistakes](#common-mistakes)
- [See also](#see-also)

## Description

Update the Environment Template to move from local Credentials to External Credentials.

In the Template Repository you:

1. identify used `credId` values, their structure, and source;
2. create a Credential Template;
3. add `external_credential_template` to the Template Descriptor;
4. replace local references with `$type: credRef`;
5. publish a new concrete version of the Environment Template.

Secret Store setup and changes to Shared Credentials, Cloud Passport Credentials, and System
Credentials happen in the Instance Repository.

System Credentials for the Template Repository itself are not migrated and remain local-only.

## Prerequisites

Before you start the migration, confirm you know:

- EnvGene version is updated to `<version>`;
- the Environment Template to migrate;
- the matching Template Descriptor;
- the Secret Store identifier, for example `default_store`;
- Credentials that come from Cloud Passport or Shared Credentials;
- the current Environment Template version;
- the template build pipeline.

Specification:

[External Credentials Management](/docs/features/external-creds.md).

Example:

[Sample template repository](/docs/samples/external-credentials/template-repository/).

## Step 1. Analyse used Credentials

Identify Cloud, Namespace, Tenant, and ParameterSet templates that belong to the selected Environment
Template.

### 1.1. Find local Credential references

Check for:

```text
${creds.get('<credId>').username}
${creds.get('<credId>').password}
${creds.get('<credId>').secret}
```

### 1.2. Find built-in Credential references

Check string references in standard EnvGene fields:

```yaml
defaultCredentialsId: k8s-token
```

```yaml
credentialsId: namespace-deploy-cred
```

```yaml
tokenSecret: consul-token
```

Built-in references include, in particular:

- `Cloud.defaultCredentialsId`;
- `Cloud.maasConfig.credentialsId`;
- `Cloud.dbaasConfigs[].credentialsId`;
- `Cloud.vaultConfig.credentialsId`;
- `Cloud.consulConfig.tokenSecret`;
- `Namespace.credentialsId`;
- `Tenant.credential`;
- `BGDomain.controllerNamespace.credentials`.

A built-in reference contains only `credId`.

A Credential with that `credId` must be defined in one of these sources:

- Credential Template;
- Cloud Passport Credentials;
- Shared Credentials.

If the Credential comes from Cloud Passport or Shared Credentials, do not add it to the Credential
Template.

> [!IMPORTANT]
> After you add `external_credential_template`, every used `credId` must be declared explicitly in at
> least one source. Otherwise Environment Instance generation fails with an error.

### 1.3. Determine Credential structure

Determine structure from current references:

| Local reference             | External Credential     |
|-----------------------------|-------------------------|
| `.username` and `.password` | Multi-field Credential  |
| `.secret`                   | Single-value Credential |

For a multi-field Credential use:

```yaml
properties:
  - name: username
  - name: password
```

For a single-value Credential, omit the `properties` field.

Do not define Credential structure from the `credId` name.

### 1.4. Determine Credential source

For each `credId`, pick one source:

- Credential Template;
- Cloud Passport Credentials;
- Shared Credentials.

If one `credId` appears in multiple sources, confirm which source should be used.

Do not add a Credential to the Credential Template when the source is not yet determined.

### 1.5. Check constraints

Credential Reference is supported only in:

- `deployParameters`;
- `e2eParameters`.

Credential Reference is not supported in:

```yaml
technicalConfigurationParameters:
```

Do not move a Credential automatically from `technicalConfigurationParameters` into another block.

Template composition for External Credentials is out of scope.

> [!WARNING]
> External Credentials migration for BG deployment cases is out of scope.

**Result:** used `credId` values, their structure, source, and unsupported cases are identified.

## Step 2. Create Credential Template

Create one Credential Template for the selected Environment Template.

Example path:

```text
templates/env_templates/<solution>/external-credentials.yml.j2
```

Add only Credentials that should be generated from this Environment Template.

### 2.1. Multi-field Credential

```yaml
---
app-db-cred:
  type: external
  secretStore: default_store
  properties:
    - name: username
    - name: password
```

### 2.2. Single-value Credential

```yaml
app-token:
  type: external
  secretStore: default_store
```

For a single-value Credential, omit the `properties` field.

### 2.3. Credential with explicit `remoteRefPath`

```yaml
app-db-cred:
  type: external
  secretStore: default_store
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}/database"
  properties:
    - name: username
    - name: password
```

If `remoteRefPath` is omitted, EnvGene uses:

```text
{{ current_env.cloud }}/{{ current_env.name }}
```

EnvGene builds `normalizedSecretName` from `remoteRefPath` and `credId` according to the selected Secret
Store rules.

For example, for Vault:

```text
<remoteRefPath>/<credId>
```

Do not append `credId` to the end of `remoteRefPath` manually.

### 2.4. Credential Template rules

The Credential Template must follow these rules:

- one Credential Template per Environment Template;
- top-level key is `credId`;
- `type` is `external`;
- `data` and secret values are absent;
- multi-field Credentials contain `username` and `password`;
- single-value Credentials omit `properties`;
- each Credential structure is defined from references;
- Credentials from Cloud Passport or Shared Credentials are not duplicated;
- Template Repository System Credentials are not added.

For existing Credentials, do not set `create`.

When `create` is absent, the strategy is:

```text
fail_if_absent
```

The secret must be prepared in the external Secret Store by a separate process.

**Result:** a Credential Template with External Credentials generated by the Environment Template is
created.

## Step 3. Update Template Descriptor

Add the Credential Template path to the Template Descriptor:

```yaml
external_credential_template: "{{ templates_dir }}/env_templates/<solution>/external-credentials.yml.j2"
```

After you add `external_credential_template`, EnvGene disables automatic generation of local placeholder
Credentials:

```yaml
data: envgeneNullValue
```

Now every `credId` used through:

- built-in Credential reference;
- `$type: credRef`;
- `${creds.get(...)}`;

must be declared explicitly in one of these sources:

- Credential Template;
- Cloud Passport Credentials;
- Shared Credentials.

**Result:** the Template Descriptor uses the Credential Template and placeholder auto-generation is
disabled.

## Step 4. Replace local Credential references

Replace local Credential references with `$type: credRef` in `deployParameters` and `e2eParameters`.

### 4.1. Username

Before migration:

```yaml
DB_USERNAME: "${creds.get('app-db-cred').username}"
```

After migration:

```yaml
DB_USERNAME:
  $type: credRef
  credId: app-db-cred
  property: username
```

### 4.2. Password

Before migration:

```yaml
DB_PASSWORD: "${creds.get('app-db-cred').password}"
```

After migration:

```yaml
DB_PASSWORD:
  $type: credRef
  credId: app-db-cred
  property: password
```

### 4.3. Single-value Credential

Before migration:

```yaml
APP_TOKEN: "${creds.get('app-token').secret}"
```

After migration:

```yaml
APP_TOKEN:
  $type: credRef
  credId: app-token
```

For a single-value Credential, omit the `property` field.

### 4.4. Built-in references

Built-in references keep the string format.

Before migration:

```yaml
defaultCredentialsId: k8s-token
```

After migration:

```yaml
defaultCredentialsId: k8s-token
```

You change the Credential definition in the matching source, not the built-in reference.

**Result:** local Credential references are replaced with Credential References in supported parameters.

## Step 5. Verify changes

### Template Descriptor

Confirm that:

- `external_credential_template` is added;
- the path points to an existing Credential Template.

### Credential Template

Confirm that:

- the file parses and renders correctly;
- every entry has `type: external`;
- `data` and secret values are absent;
- multi-field Credentials contain `username` and `password`;
- single-value Credentials omit `properties`;
- each Credential structure is confirmed from references;
- Credentials from Cloud Passport and Shared Credentials are not duplicated;
- `remoteRefPath` does not end with a manually appended `credId`.

### Credential references

Confirm that:

- local references are replaced in `deployParameters`;
- local references are replaced in `e2eParameters`;
- `$type: credRef` is absent from `technicalConfigurationParameters`;
- built-in references remain strings.

### Coverage and conflicts

Confirm that:

- every used `credId` is defined in the Credential Template, Cloud Passport, or Shared Credentials;
- one `credId` does not have conflicting structures;
- the source of each `credId` is determined;
- the Credential Template does not contain Credentials that should come from Cloud Passport or Shared
  Credentials.

**Result:** the Template is ready to build and publish.

## Step 6. Publish new Template version

Run the template build pipeline manually.

After a successful build, note the concrete artifact version:

```text
<artifactId>:<version>
```

Do not use `SNAPSHOT` to switch Environment Instances.

Hand the concrete version to the Instance Repository owner.

**Result:** a concrete version of the Environment Template with External Credentials support is
published.

## Rollback

If no Environment Instances use the new Template version yet, keep using the previous version.

If you find an error in the published version:

1. do not switch Environment Instances to that version;
2. fix the Environment Template;
3. publish a new concrete version;
4. use the corrected version.

## Common mistakes

| Mistake                                                | Fix                                              |
|--------------------------------------------------------|--------------------------------------------------|
| Used `credId` is not declared                          | Add the Credential to one of the sources         |
| `username` and `password` added for all Credentials    | Define each Credential structure from references |
| Cloud Passport Credential added to Credential Template | Remove the duplicate                             |
| Local reference left in a parameter                    | Replace with `$type: credRef`                    |
| `credRef` added to `technicalConfigurationParameters`  | Revert the change                                |
| Built-in reference replaced with an object             | Restore the string `credId`                      |
| Incorrect `properties`                                 | Fix the Credential structure                     |
| `credId` appended to `remoteRefPath`                   | Remove it from the path                          |

## See also

- [Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md)
- [External Credentials Management](/docs/features/external-creds.md)
- [Credential Template](/docs/envgene-objects.md#credential-template)
- [Template Descriptor](/docs/envgene-objects.md#template-descriptor)
- [Sample external credentials template repository](/docs/samples/external-credentials/template-repository/)
