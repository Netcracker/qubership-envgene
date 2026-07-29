# Migrate Template Repository to External Credentials

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Step 1. Select Environment Templates](#step-1-select-environment-templates)
- [Step 2. Find used Credentials](#step-2-find-used-credentials)
- [Step 3. Create the Credential Template](#step-3-create-the-credential-template)
- [Step 4. Update the Template Descriptor](#step-4-update-the-template-descriptor)
- [Step 5. Replace macros in templates and ParameterSets](#step-5-replace-macros-in-templates-and-parametersets)
- [Step 6. Verify and publish](#step-6-verify-and-publish)
- [Rollback](#rollback)
- [Common mistakes](#common-mistakes)
- [See also](#see-also)

## Description

Migrate Environment Templates in the Template Repository so they use External Credentials.

For each Environment Template:

1. find local Credential macros and Built-in Credential references
2. create a Credential Template with matching External Credentials
3. point the Template Descriptor at that file
4. replace supported macros with `$type: credRef`
5. publish a concrete Template version

Repeat the same flow for every Environment Template you migrate.

`$type: credRef` works only in `deployParameters`, `e2eParameters`, and ParameterSets that feed
those blocks. It does not work in `technicalConfigurationParameters`.

Built-in fields such as `credentialsId`, `defaultCredentialsId`, `tokenSecret`, and `credential`
stay plain `credId` strings. You change the Credential definition in the Credential Template, not
those fields.

BG deployment and template composition are out of scope for this guide.

System Credentials in the Template Repository stay local-only.

## Prerequisites

Before you start, confirm that:

- EnvGene is upgraded to a version that includes External Credentials
- the Environment Templates and Template Descriptors to migrate are identified
- the Secret Store identifier is known, for example `default_store`
- for each Credential you know whether the secret already exists, or a new generated value is
  acceptable (`create: true`)
- the template build pipeline is available

Specification: [External Credentials Management](/docs/features/external-creds.md).

Example layout: [Sample template repository](/docs/samples/external-credentials/template-repository/).

## Step 1. Select Environment Templates

List the Environment Templates to migrate. For each one, open its Template Descriptor and note the
paths of its Cloud, Namespace, Tenant, and ParameterSet templates.

Work through the remaining steps per Environment Template, then publish that Template before you
move to the next one when versions must stay independent.

**Result:** Environment Templates selected for migration.

## Step 2. Find used Credentials

In the Cloud, Namespace, Tenant, and ParameterSet templates for the current Environment Template,
search for:

```text
${creds.get('<credId>').username}
${creds.get('<credId>').password}
${creds.get('<credId>').secret}
```

Also search for `${envgen.creds.get(...)}` and `${cmdb.creds.get(...)}`.

Search for Built-in Credential references. Examples:

```yaml
credentialsId: ns-deploy-cred
```

```yaml
credential: tenant-cred
```

Built-in fields include:

- `Cloud.defaultCredentialsId`
- `Cloud.maasConfig.credentialsId`
- `Cloud.dbaasConfigs[].credentialsId`
- `Cloud.vaultConfig.credentialsId`
- `Cloud.consulConfig.tokenSecret`
- `Namespace.credentialsId`
- `Tenant.credential`

Leave these fields as plain `credId` strings. Do not convert them to `$type: credRef`.

When a Built-in field has no `.username` / `.password` / `.secret` macro nearby, use these structure
hints:

| Built-in field                         | Credential Template shape |
|----------------------------------------|---------------------------|
| `maasConfig.credentialsId`             | multi-field               |
| `dbaasConfigs[].credentialsId`         | multi-field               |
| `vaultConfig.credentialsId`            | single-value              |
| `consulConfig.tokenSecret`             | single-value              |
| `Namespace.credentialsId`              | single-value              |
| `Tenant.credential`                    | single-value              |
| `Cloud.defaultCredentialsId`           | confirm from other usages |

For each `credId`, note the file and the structure from the reference. Do not guess structure from
the name:

| Local reference             | Credential Template shape                          |
|-----------------------------|----------------------------------------------------|
| `.username` and `.password` | multi-field (`properties`)                         |
| `.secret`                   | single-value (no `properties`)                     |
| Built-in string field only  | take structure from other usages of the same `credId` |

Also mark unsupported usages: macros inside `technicalConfigurationParameters` or ParameterSets used
only through `technicalConfigurationParameterSets`. Do not replace those with `$type: credRef` or
with plain-text secrets in Git. Resolve them separately before you publish.

**Result:** list of `credId` values, structures, and unsupported cases for this Environment Template.

## Step 3. Create the Credential Template

Create one Credential Template file per Environment Template.

Example path:

```text
templates/env_templates/<solution>/external-credentials.yml.j2
```

Before migration, EnvGene often auto-creates local placeholders during Instance generation, for
example:

```yaml
app-db-cred:
  type: usernamePassword
  data:
    username: envgeneNullValue
    password: envgeneNullValue
```

After migration, declare the Credentials explicitly. Match the sample shape:

```yaml
---
app-db-cred:
  type: external
  create: true
  secretStore: default_store
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}/db"
  properties:
    - name: username
    - name: password
app-sidecar-token:
  type: external
  create: true
  secretStore: default_store
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}/sidecar"
ns-deploy-cred:
  type: external
  create: true
  secretStore: default_store
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"
tenant-cred:
  type: external
  create: true
  secretStore: default_store
  remoteRefPath: "{{ current_env.cloud }}"
```

Rules:

- top-level key is `credId`
- `type` is `external`
- no `data` and no secret values
- multi-field Credentials use:

  ```yaml
  properties:
    - name: username
    - name: password
  ```

  never `- username` / `- password` as bare strings
- single-value Credentials omit `properties`
- if `secretStore` is omitted, EnvGene uses `default_store`
- if `remoteRefPath` is omitted, EnvGene uses `{{ current_env.cloud }}/{{ current_env.name }}`
- do not append `credId` to `remoteRefPath` - EnvGene adds it when building the final secret name
- for Azure, AWS, and GCP, keep `credId` to at most 32 characters (see
  [Normalization to normalizedSecretName](/docs/features/external-creds.md#normalization-to-normalizedsecretname))
- add only Credentials that this Environment Template owns
- do not copy Credentials that already live in Cloud Passport or Shared Credentials

`create`:

- omit `create` when the secret already exists in the Secret Store
- set `create: true` when a new generated secret value is acceptable

`create` and `remoteRefPath` are independent. If you omit `remoteRefPath`, EnvGene still uses
`{{ current_env.cloud }}/{{ current_env.name }}`, whether `create` is set or not.

**Result:** Credential Template file created for this Environment Template.

## Step 4. Update the Template Descriptor

Before:

```yaml
tenant: "{{ templates_dir }}/env_templates/<solution>/tenant.yml.j2"
cloud: "{{ templates_dir }}/env_templates/<solution>/cloud.yml.j2"
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/<solution>/ns.yml.j2"
```

After:

```yaml
tenant: "{{ templates_dir }}/env_templates/<solution>/tenant.yml.j2"
cloud: "{{ templates_dir }}/env_templates/<solution>/cloud.yml.j2"
external_credential_template: "{{ templates_dir }}/env_templates/<solution>/external-credentials.yml.j2"
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/<solution>/ns.yml.j2"
```

After this field is set, EnvGene stops auto-creating local placeholder Credentials with
`data: envgeneNullValue`.

> [!IMPORTANT]
> Every `credId` used through a Built-in reference, `$type: credRef`, or `${creds.get(...)}` must be
> declared in the Credential Template or later in Cloud Passport / Shared Credentials. Otherwise
> Environment Instance generation fails.

**Result:** Template Descriptor references the Credential Template.

## Step 5. Replace macros in templates and ParameterSets

Replace macros only in `deployParameters`, `e2eParameters`, and ParameterSets from
`deployParameterSets` / `e2eParameterSets`. Leave Built-in string fields unchanged.

### Namespace template

Before:

```yaml
deployParameters:
  DB_ADMIN_USER: "${creds.get('app-db-cred').username}"
  DB_ADMIN_PASSWORD: "${creds.get('app-db-cred').password}"
```

After:

```yaml
credentialsId: ns-deploy-cred
deployParameters:
  DB_ADMIN_USER:
    $type: credRef
    credId: app-db-cred
    property: username
  DB_ADMIN_PASSWORD:
    $type: credRef
    credId: app-db-cred
    property: password
```

### ParameterSet

Before:

```yaml
name: ext-cred-cloud
parameters:
  INTEGRATION_TOKEN: "${creds.get('app-sidecar-token').secret}"
```

After:

```yaml
name: ext-cred-cloud
parameters:
  INTEGRATION_TOKEN:
    $type: credRef
    credId: app-sidecar-token
```

Check `parameters` and `applications[].parameters`.

For a single-value Credential, omit `property` on the Credential Reference.

**Result:** supported macros replaced with `$type: credRef`. Built-in references still strings.

## Step 6. Verify and publish

Confirm that:

- `external_credential_template` points to the Credential Template file
- every Credential Template entry has `type: external` and no `data`
- multi-field and single-value shapes match the usages from Step 2
- supported macros are replaced
- technical configuration has no `$type: credRef`
- Built-in references remain strings
- `remoteRefPath` does not end with a manually appended `credId`

Run the template build pipeline and publish a concrete version:

```text
<artifactId>:<version>
```

Do not use `SNAPSHOT` for Instance Repository cutover.

Then continue with
[Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md)
for the Instance Repository that consumes this Template version.

**Result:** concrete Template version published.

## Rollback

If no Environment Instance uses the new version yet, keep the previous version.

If the published version is wrong:

1. do not switch Environment Instances to it
2. fix the Environment Template
3. publish a new concrete version

## Common mistakes

| Mistake                                            | Fix                                         |
|----------------------------------------------------|---------------------------------------------|
| `credId` used but missing from Credential Template | Add it to the Credential Template           |
| `properties: [username, password]`                 | Use `- name: username` / `- name: password` |
| Structure guessed from `credId`                    | Use the macro or Built-in usage             |
| Macro left in supported parameters                 | Replace with `$type: credRef`               |
| `credRef` in technical configuration               | Do not convert. Relocate the parameter      |
| Built-in field turned into an object               | Keep the string `credId`                    |
| `credId` appended to `remoteRefPath`               | Remove the suffix                           |
| `create: true` when the old secret must stay       | Omit `create` and prepare the secret first  |

## See also

- [Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md)
- [External Credentials Management](/docs/features/external-creds.md)
- [Credential Template](/docs/envgene-objects.md#credential-template)
- [Template Descriptor](/docs/envgene-objects.md#template-descriptor)
- [Sample external credentials template repository](/docs/samples/external-credentials/template-repository/)
