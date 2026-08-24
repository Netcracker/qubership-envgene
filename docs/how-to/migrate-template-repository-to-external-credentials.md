# Migrate Template Repository to External Credentials

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Step 1. Collect credential IDs](#step-1-collect-credential-ids)
- [Step 2. Decide create and remoteRefPath](#step-2-decide-create-and-remoterefpath)
- [Step 3. Create the Credential Template](#step-3-create-the-credential-template)
- [Step 4. Register in the Template Descriptor](#step-4-register-in-the-template-descriptor)
- [Step 5. Replace macros](#step-5-replace-macros)
- [Step 6. Verify and publish](#step-6-verify-and-publish)
- [Rollback](#rollback)
- [See also](#see-also)

## Description

Migrate Environment Templates in the Template Repository to External Credentials.

Work through Steps 1-6 for one Environment Template, then repeat for the next.

For each Environment Template:

1. collect every credential ID and its structure
2. decide who creates the value, `create`, and `remoteRefPath`
3. create one Credential Template file
4. register that file in the Template Descriptor
5. replace credential macros with `$type: credRef`
6. verify and publish a concrete Template version

`$type: credRef` works only in `deployParameters`, `e2eParameters`, and ParameterSets that feed
those blocks. It does not work in `technicalConfigurationParameters`.

Built-in fields stay plain `credId` strings. You change the Credential definition in the Credential
Template, not those fields.

System Credentials in the Template Repository stay local-only. BG deployment and template composition
are out of scope.

## Prerequisites

Confirm before you start:

- the Secret Store identifier you use is known and matches
  `/configuration/secret-stores.yml` in consuming Instance Repositories
- you have write access to the Template Repository
- the Template Descriptors for the templates you are migrating are identified
- for each Credential you know the creation owner (EnvGene may generate, secret must pre-exist,
  or an external provider creates it) before you write the Credential Template

Specification: [External Credentials Management](/docs/features/external-creds.md).

Example layout: [Sample template repository](/docs/samples/external-credentials/template-repository/).

## Step 1. Collect credential IDs

Open the Cloud, Namespace, Tenant, and ParameterSet templates for this Environment Template.

Search for all credential references. There are three kinds.

### Macros in parameter values

You replace these in Step 4:

```text
${creds.get('<credId>').username}
${creds.get('<credId>').password}
${creds.get('<credId>').secret}
${envgen.creds.get('<credId>').username|password|secret}
${cmdb.creds.get('<credId>').username|password|secret}
```

### Legacy macro keys

You replace these in Step 4. The value is the `credId`:

```text
'#creds{PARAM_LOGIN, PARAM_PASSWORD}': <credId>
'#credscl{PARAM_LOGIN, PARAM_PASSWORD}': <credId>
'#credsns{PARAM_LOGIN, PARAM_PASSWORD}': <credId>
```

### Built-in string fields

Leave as-is - record the `credId` only:

```yaml
credentialsId: <credId>
defaultCredentialsId: <credId>
tokenSecret: <credId>
credential: <credId>
```

The canonical list is in
[Built-in credential references](/docs/features/external-creds.md#built-in-credential-references).

### Structure

For each `credId`, record its structure:

| If the credId appears with                           | Structure                                      |
|------------------------------------------------------|------------------------------------------------|
| `.username` / `.password`, or as a `#creds*` key     | multi-field                                    |
| `.secret`                                            | single-value                                   |
| Built-in field only                                  | use the Built-in shape below, or other usages  |
| `Cloud.defaultCredentialsId` only                    | confirm from other usages of the same `credId` |

Built-in shape hints when there is no nearby `.username` / `.password` / `.secret` macro:

| Built-in field                   | Structure    |
|----------------------------------|--------------|
| `maasConfig.credentialsId`       | multi-field  |
| `dbaasConfigs[].credentialsId`   | multi-field  |
| `vaultConfig.credentialsId`      | single-value |
| `consulConfig.tokenSecret`       | single-value |
| `Namespace.credentialsId`        | single-value |
| `Tenant.credential`              | single-value |

Build a table as you go:

| credId              | Structure    | Location                              |
|---------------------|--------------|---------------------------------------|
| app-db-cred         | multi-field  | `ns.yml.j2`, `deployParameters`       |
| app-sidecar-token   | single-value | paramset, `deployParameters`          |
| ns-deploy-cred      | single-value | `ns.yml.j2`, built-in `credentialsId` |

Skip macros inside `technicalConfigurationParameters`. Do not convert those. Resolve them separately
before publishing.

**Result:** a complete table of `credId`, structure, and location.

## Step 2. Decide create and remoteRefPath

Before you write the Credential Template, decide for each Template-owned Credential:

1. **Scope** - Template-owned Environment Credentials are environment-scoped.
2. **Who creates the value** - EnvGene (new value allowed), pre-existing (must exist in the Store),
   or provider (external system creates it).
3. **`create`** - see the matrix below.
4. **`remoteRefPath`** - prefix only. EnvGene appends the normalised `credId`.
5. **Review ambiguous cases** - do not guess. Confirm with the owner or Platform team.

### Decision matrix

| Who creates the value | In your plan / notes | In Credential Template YAML |
|-----------------------|----------------------|-----------------------------|
| EnvGene may generate a new value | `create: true` | `create: true` |
| Secret must already exist | `create: false` | omit `create` |
| External provider creates it | `create: false` | omit `create` |
| Unknown | do not write the entry yet | leave unchanged |

`create` controls EnvGene runtime when the secret is absent (`true` generates, omitted/`false`
means verify and fail if missing). It does **not** mean "copy plaintext from Git into the Store".
If you transfer an existing Git value into the Store during migration, track that transfer
separately (for example a migration checklist flag). That transfer flag never appears in the
Credential Template YAML.

### Template path defaults

For Template-owned Environment Credentials propose:

```text
{{ current_env.cloud }}/{{ current_env.name }}
```

Add a static suffix only when you have a confirmed scope (for example `/db`). Do not append
`credId`. Do not use `{{ current_env.namespace }}` unless your EnvGene version documents that
variable in this Jinja context.

Do not put Cloud Passport or Shared Credentials into the Credential Template only because the
template references them. Record ownership for the Instance Repository migration instead.

Names like `consul`, `dbaas`, or `operator` in a `credId` are review signals only. Confirm
ownership before you set `create: true` or a provider path.

**Result:** confirmed create and path decisions for every Template-owned `credId`.

## Step 3. Create the Credential Template

Create one file per Environment Template:

```text
templates/env_templates/<solution>/external-credentials.yml.j2
```

Add one entry per Template-owned `credId` from Step 1:

```yaml
---
# multi-field credential - EnvGene may generate
app-db-cred:
  type: external
  create: true
  secretStore: <your-secret-store>
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}/db"
  properties:
    - name: username
    - name: password

# single-value credential - EnvGene may generate
app-sidecar-token:
  type: external
  create: true
  secretStore: <your-secret-store>
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"

# existing or provider-managed secret - omit create
ns-deploy-cred:
  type: external
  secretStore: <your-secret-store>
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"
```

Rules:

- `type` is always `external`. No `data` block, no secret values in Git.
- multi-field: use `- name: username` / `- name: password`. Never bare strings (`- username`).
- single-value: omit `properties` entirely.
- `create: true` only when EnvGene generation of a new value is confirmed.
- omit `create` when the secret must already exist or a provider creates it. Do not write
  `create: false` in the YAML.
- if `secretStore` is omitted, EnvGene uses `default_store`.
- default `remoteRefPath` for Template-owned credentials:
  `{{ current_env.cloud }}/{{ current_env.name }}`.
- do not append the `credId` to `remoteRefPath` - EnvGene adds it automatically.
- on Azure / AWS / GCP: keep each `credId` to 32 characters or fewer.

**Result:** Credential Template file created.

## Step 4. Register in the Template Descriptor

In the Template Descriptor for this Environment Template, add `external_credential_template`.

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

Once this field is set, EnvGene stops auto-creating local placeholder credentials.

> [!IMPORTANT]
> Every `credId` referenced in the template must now be declared in the Credential Template -
> otherwise generation fails.

**Result:** Template Descriptor points to the Credential Template.

## Step 5. Replace macros

Replace macros only in `deployParameters`, `e2eParameters`, and ParameterSets from
`deployParameterSets` / `e2eParameterSets`.

Do not touch: built-in fields (`credentialsId`, `defaultCredentialsId`, `tokenSecret`, `credential`)
and anything inside `technicalConfigurationParameters`.

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

For `.secret` (single-value) - omit `property`:

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

All three variants (`#creds`, `#credscl`, `#credsns`) expand the same way - one key becomes two
`credRef` entries: `username` and `password`.

**Result:** all supported macros replaced. Built-in fields still plain strings.

## Step 6. Verify and publish

Confirm that:

- every Template-owned Credential has a confirmed creation owner, `create` decision, and path
- `external_credential_template` path in the Template Descriptor is correct
- every `credId` from Step 1 that belongs in the Credential Template is present
- every entry has `type: external` and no `data` block
- multi-field credentials use `- name: username` / `- name: password`
- all `creds.get`, `cmdb.creds.get`, `#creds`, `#credscl`, `#credsns` macros are replaced
- no `$type: credRef` inside `technicalConfigurationParameters`
- built-in fields are still plain strings
- no `credId` appended to `remoteRefPath`
- no `create: false` and no transfer-only flags in the YAML
- ambiguous or provider-suspect Credentials were confirmed or left out of publish

Run the template build pipeline and publish a concrete version:

```text
<artifactId>:<version>
```

Next:
[Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md)
for the Instance Repository consuming this Template version.

**Result:** concrete Template version published.

## Rollback

If no Environment Instance uses the new version yet - keep the previous version and fix the template.

If you published a bad version:

1. do not switch any Environment Instance to it
2. fix the Environment Template
3. publish a new concrete version

## See also

- [Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md)
- [External Credentials Management](/docs/features/external-creds.md)
- [Built-in credential references](/docs/features/external-creds.md#built-in-credential-references)
- [Credential Template](/docs/envgene-objects.md#credential-template)
- [Template Descriptor](/docs/envgene-objects.md#template-descriptor)
- [Sample external credentials template repository](/docs/samples/external-credentials/template-repository/)
