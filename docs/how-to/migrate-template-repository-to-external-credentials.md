# Migrate Template Repository to External Credentials

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Step 1: Collect credential IDs](#step-1-collect-credential-ids)
- [Step 2: Decide create and remoteRefPath](#step-2-decide-create-and-remoterefpath)
- [Step 3: Create the Credential Template](#step-3-create-the-credential-template)
- [Step 4: Register in the Template Descriptor](#step-4-register-in-the-template-descriptor)
- [Step 5: Replace macros](#step-5-replace-macros)
- [Step 6: Verify and publish](#step-6-verify-and-publish)
- [Rollback](#rollback)
- [See also](#see-also)

## Description

Use this guide to move an Environment Template from credential macros to External Credentials. At the end, the
template declares its credentials in a Credential Template, references them with `$type: credRef`, and is
published as a new version.

Repeat the steps for each Environment Template.

The guide changes only the template files. The secret values stay where they are and move to the Secret Store
during [Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md).

## Prerequisites

- Every environment that uses this template is on a No-CMDB
  [deployment architecture](/docs/deployment-architecture.md). CMDB import does not work with External Credentials.
- The EnvGene version in the Instance repositories supports External Credentials.
- You know the Secret Store identifier the Instance repositories will use. Skip this if they use `default_store`.
- You have write access to the Template Repository.

For every field used below, see [External Credentials](/docs/features/external-creds.md). For a complete example, see
the [sample template repository](/docs/samples/external-credentials/template-repository/).

## Step 1: Collect credential IDs

Open the Cloud, Namespace, Tenant, and ParameterSet templates of this Environment Template and find every
credential reference. For each `credId`, record its shape, where it is used, and where it is declared. There are
three kinds of references.

### Macros in parameter values

You replace these in [Step 5](#step-5-replace-macros):

```text
${creds.get('<credId>').username}
${creds.get('<credId>').password}
${creds.get('<credId>').secret}
${envgen.creds.get('<credId>').username|password|secret}
${cmdb.creds.get('<credId>').username|password|secret}
```

### Legacy macro keys

You replace these in [Step 5](#step-5-replace-macros). The value is the `credId`:

```text
'#creds{PARAM_LOGIN, PARAM_PASSWORD}': <credId>
'#credscl{PARAM_LOGIN, PARAM_PASSWORD}': <credId>
'#credsns{PARAM_LOGIN, PARAM_PASSWORD}': <credId>
```

### Built-in string fields

Leave as-is. Record the `credId` only:

```yaml
credentialsId: <credId>
defaultCredentialsId: <credId>
tokenSecret: <credId>
credential: <credId>
```

The canonical list is in
[Built-in credential references](/docs/features/external-creds.md#built-in-credential-references).

### Shape

The shape decides whether the credential gets `properties` in Step 3:

| If the credId appears with        | Shape                                          |
|-----------------------------------|------------------------------------------------|
| `.username` or `.password`        | username and password                          |
| a `#creds*` key                   | username and password                          |
| `.secret`                         | single value                                   |
| Built-in field only               | built-in shape below, or other usages          |
| `Cloud.defaultCredentialsId` only | confirm from other usages of the same `credId` |

Built-in shape hints when there is no nearby `.username`, `.password`, or `.secret` macro:

| Built-in field                 | Shape                 |
|--------------------------------|-----------------------|
| `maasConfig.credentialsId`     | username and password |
| `dbaasConfigs[].credentialsId` | username and password |
| `vaultConfig.credentialsId`    | single value          |
| `consulConfig.tokenSecret`     | single value          |
| `Namespace.credentialsId`      | single value          |
| `Tenant.credential`            | single value          |

Build a table as you go. Check the Cloud Passport `*-creds.yml` files and the Shared Credentials files of the
Instance repositories to fill in **Declared in**: only credentials declared by the template go to the Credential
Template in Step 3.

| credId            | Shape                 | Used in                                  | Declared in    |
|-------------------|-----------------------|------------------------------------------|----------------|
| app-db-cred       | username and password | `ns.yml.j2`, `deployParameters`          | template       |
| app-sidecar-token | single value          | paramset, `deployParameters`             | template       |
| ns-deploy-cred    | single value          | `ns.yml.j2`, built-in `credentialsId`    | template       |
| dbaas-cred        | username and password | `cloud.yml.j2`, built-in `credentialsId` | Cloud Passport |

`$type: credRef` does not work in `technicalConfigurationParameters`. List the macros you find there separately
and agree with the template owner how to handle them before you publish.

**Result:** a table of every `credId` with its shape, usage, and where it is declared.

## Step 2: Decide create and remoteRefPath

Take the credentials from the Step 1 table that are declared in the template. Skip the ones declared in the Cloud
Passport or Shared Credentials: they move in the Instance repository migration.

For each credential, decide two values.

### `create`

| Who creates the value                               | In the Credential Template           |
|-----------------------------------------------------|--------------------------------------|
| EnvGene may generate a new value                    | `create: true`                       |
| The secret already exists, or a provider creates it | omit `create`                        |
| You do not know                                     | stop and ask the owner before Step 3 |

`create` only says what EnvGene does when the secret is missing. Moving existing values into the store is part of
[Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md).

### `remoteRefPath`

Use the path of the environment:

```text
{{ current_env.cloud }}/{{ current_env.name }}
```

Add a suffix, such as `/db`, only to group credentials. Do not append the `credId`: EnvGene adds it. Do not use
`current_env.namespace`: it is not an EnvGene macro.

**Result:** a `create` value and a `remoteRefPath` for every credential declared in the template.

## Step 3: Create the Credential Template

Create one file per Template Descriptor, named after it: for `bss.yaml`, create
`templates/external-credentials/bss.yml.j2`.

Add one entry per credential from Step 2:

```yaml
---
# username and password, EnvGene may generate
app-db-cred:
  type: external
  create: true
  secretStore: default_store
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}/db"
  properties:
    - name: username
    - name: password
# single value, EnvGene may generate
app-sidecar-token:
  type: external
  create: true
  secretStore: default_store
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"
# single value, already in the store
ns-deploy-cred:
  type: external
  secretStore: default_store
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"
```

For a single value, leave out `properties`. For the rules of every field, see
[Credential](/docs/features/external-creds.md#credential).

**Result:** the Credential Template file with one entry per credential declared in the template.

## Step 4: Register in the Template Descriptor

In the Template Descriptor for this Environment Template, add `external_credential_template` with
the path to the Credential Template from Step 3.

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
external_credential_template: "{{ templates_dir }}/external-credentials/<solution>.yml.j2"
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/<solution>/ns.yml.j2"
```

> [!IMPORTANT]
> From now on, every `credId` the template references must be declared for each environment: in the Credential
> Template, the Cloud Passport, or the Shared Credentials. Otherwise generation fails.

**Result:** Template Descriptor points to the Credential Template.

## Step 5: Replace macros

Replace macros only in `deployParameters`, `e2eParameters`, and ParameterSets from
`deployParameterSets` or `e2eParameterSets`.

Do not touch built-in fields (`credentialsId`, `defaultCredentialsId`, `tokenSecret`, `credential`)
or anything inside `technicalConfigurationParameters`.

### `creds.get` / `envgen.creds.get` / `cmdb.creds.get`

Before:

```yaml
DB_USER: "${creds.get('app-db-cred').username}"
DB_PASS: "${creds.get('app-db-cred').password}"
```

After:

```yaml
DB_USER:
  $type: credRef
  credId: app-db-cred
  property: username
DB_PASS:
  $type: credRef
  credId: app-db-cred
  property: password
```

For `.secret` (a single value), leave out `property`:

```yaml
INTEGRATION_TOKEN:
  $type: credRef
  credId: app-sidecar-token
```

### `#creds` / `#credscl` / `#credsns` keys

Before:

```yaml
'#creds{LOGIN, PASSWORD}': test-cred
```

After:

```yaml
LOGIN:
  $type: credRef
  credId: test-cred
  property: username
PASSWORD:
  $type: credRef
  credId: test-cred
  property: password
```

All three variants (`#creds`, `#credscl`, `#credsns`) expand the same way. One key becomes two
`credRef` entries: `username` and `password`.

**Result:** no credential macros left in `deployParameters`, `e2eParameters`, and their ParameterSets.

## Step 6: Verify and publish

1. Check the template:
    - `external_credential_template` in the Template Descriptor points to the file from Step 3
    - every credential declared in the template, from Step 2, has an entry in the Credential Template
    - no `${creds.get(...)}`, `envgen.creds.get`, `cmdb.creds.get`, or `#creds*` macros are left in
      `deployParameters`, `e2eParameters`, and their ParameterSets
    - no `$type: credRef` in `technicalConfigurationParameters`
    - built-in fields such as `credentialsId` still hold a plain `credId`
2. Run the template build pipeline and publish a new version, for example `project-env-template:2.0.0`.

Next, migrate each Instance repository that uses this template, see
[Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md).

**Result:** a new template version on External Credentials.

## Rollback

If no Environment Instance uses the new version yet, keep the previous version and fix the template.

If you published a bad version:

1. do not switch any Environment Instance to it
2. fix the Environment Template
3. publish a new version

## See also

- [Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md)
- [External Credentials](/docs/features/external-creds.md)
- [Built-in credential references](/docs/features/external-creds.md#built-in-credential-references)
- [Credential Template](/docs/envgene-objects.md#credential-template)
- [Template Descriptor](/docs/envgene-objects.md#template-descriptor)
- [Sample external credentials template repository](/docs/samples/external-credentials/template-repository/)
