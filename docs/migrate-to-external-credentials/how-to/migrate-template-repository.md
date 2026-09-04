# Migrate Template Repository to External Credentials

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Step 1. Run preflight](#step-1-run-preflight)
- [Step 2. Collect credential IDs](#step-2-collect-credential-ids)
- [Step 3. Decide create and remoteRefPath](#step-3-decide-create-and-remoterefpath)
- [Step 4. Create the Credential Template](#step-4-create-the-credential-template)
- [Step 5. Register in the Template Descriptor](#step-5-register-in-the-template-descriptor)
- [Step 6. Replace macros](#step-6-replace-macros)
- [Step 7. Verify and publish](#step-7-verify-and-publish)
- [Rollback](#rollback)
- [See also](#see-also)

## Description

Migrate Environment Templates in the Template Repository to External Credentials.

Work through Steps 1-7 for one Environment Template, then repeat for the next.

For each Environment Template:

1. run preflight and clear blockers
2. collect every credential ID and its structure
3. decide who creates the value, `create`, and `remoteRefPath`
4. create one Credential Template file
5. register that file in the Template Descriptor
6. replace credential macros with `$type: credRef`
7. verify and publish a concrete Template version

`$type: credRef` works only in `deployParameters`, `e2eParameters`, and ParameterSets that feed
those blocks. It does not work in `technicalConfigurationParameters`.

Built-in fields stay plain `credId` strings. You change the Credential definition in the Credential
Template, not those fields.

System Credentials in the Template Repository stay local-only. BG deployment and template composition
are out of scope.

## Prerequisites

Confirm before you start:

- the consuming Instance Repository uses one `default_store` in `/configuration/secret-stores.yml`
- you have write access to the Template Repository
- the Template Descriptors for the templates you are migrating are identified
- for each Credential you know the creation owner (EnvGene may generate, secret must pre-exist,
  or an external provider creates it) before you write the Credential Template

Specification: [External Credentials Management](/docs/features/external-creds.md).

Example layout: [Sample template repository](/docs/samples/external-credentials/template-repository/).

## Step 1. Run preflight

From the Template Repository root (or via the migration skill scripts directory), run:

```bash
python docs/migrate-to-external-credentials/skills/template-repository/scripts/preflight.py --repo .
```

The check is read-only. It starts from Template Descriptors and follows referenced Cloud, Namespace,
Tenant templates and ParameterSets bound through `deployParameterSets` / `e2eParameterSets`.

It reports blockers such as:

- missing files referenced by the descriptor
- composite credential macros (macro embedded in a larger string)
- structure conflicts (same `credId` used as multi-field and single-value)
- ParameterSet files with credential refs that are not bound from scanned templates
- `{{ current_env.namespace }}` in an existing Credential Template `remoteRefPath`
- `data` or `writeToStore` in an existing Credential Template

Exit code `2` means fix blockers and re-run. Do not draft the Credential Template until exit `0`.

**Result:** preflight status `ok` (warnings may remain for review).

## Step 2. Collect credential IDs

Open the Cloud, Namespace, Tenant, and ParameterSet templates for this Environment Template.

Search for all credential references. There are three kinds.

### Macros in parameter values

You replace these in Step 6:

```text
${creds.get('<credId>').username}
${creds.get('<credId>').password}
${creds.get('<credId>').secret}
${envgen.creds.get('<credId>').username|password|secret}
${cmdb.creds.get('<credId>').username|password|secret}
```

### Legacy macro keys

You replace these in Step 6. The value is the `credId`:

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

## Step 3. Decide create and remoteRefPath

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
means verify and fail if missing). It does **not** mean "copy passwords or tokens from Git into the
Store".
If you transfer an existing Git value into the Store during migration, track that transfer
separately (for example a migration checklist flag). That transfer flag never appears in the
Credential Template YAML.

### Template path defaults

For Template-owned Environment Credentials propose:

```text
{{ current_env.cloud }}/{{ current_env.name }}
```

Add a static suffix only when you have a confirmed scope (for example `/db`). Do not append
`credId`.

EnvGene does not expose `{{ current_env.namespace }}` in the Credential Template Jinja context.
Do not use it in `remoteRefPath`, even as a manual override - rendering will fail or produce
wrong paths. Per-namespace Store granularity belongs in Instance Repository migration
(`remoteRefPath` on env-tier Shared Credentials) or a confirmed static suffix segment.

Do not put Cloud Passport or Shared Credentials into the Credential Template only because the
template references them. Record ownership for the Instance Repository migration instead.

Names like `consul`, `dbaas`, or `operator` in a `credId` are review signals only. Confirm
ownership before you set `create: true` or a provider path.

**Result:** confirmed create and path decisions for every Template-owned `credId`.

## Step 4. Create the Credential Template

Create one file per Template Descriptor. The filename stem matches the descriptor stem
(`bss.yaml` descriptor → `bss.yml.j2`):

```text
templates/external-credentials/<descriptor-stem>.yml.j2
```

Add one entry per Template-owned `credId` from Step 2:

```yaml
---
# multi-field credential - EnvGene may generate
app-db-cred:
  type: external
  create: true
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}/db"
  properties:
    - name: username
    - name: password

# single-value credential - EnvGene may generate
app-sidecar-token:
  type: external
  create: true
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"

# existing or provider-managed secret - omit create
ns-deploy-cred:
  type: external
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"
```

Rules:

- `type` is always `external`. No `data` block, no secret values in Git.
- multi-field: use `- name: username` / `- name: password`. Never bare strings (`- username`).
- single-value: omit `properties` entirely.
- `create: true` only when EnvGene generation of a new value is confirmed.
- omit `create` when the secret must already exist or a provider creates it. Do not write
  `create: false` in the YAML.
- set `secretStore: default_store` on each entry (or another confirmed store id). Schema default
  exists, but the Effective Set calculator has no runtime fallback.
- default `remoteRefPath` for Template-owned credentials:
  `{{ current_env.cloud }}/{{ current_env.name }}`.
- do not append the `credId` to `remoteRefPath` - EnvGene adds it automatically.
- on Azure / AWS / GCP: keep each `credId` to 32 characters or fewer.

**Result:** Credential Template file created.

## Step 5. Register in the Template Descriptor

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
external_credential_template: "{{ templates_dir }}/external-credentials/<descriptor-stem>.yml.j2"
namespaces:
  - template_path: "{{ templates_dir }}/env_templates/<solution>/ns.yml.j2"
```

Convention: the Credential Template stem matches the Template Descriptor stem (`dev.yaml` →
`dev.yml.j2`).

Once this field is set, EnvGene stops auto-creating local placeholder credentials.

> [!IMPORTANT]
> Every `credId` referenced in the template must now be declared in the Credential Template -
> otherwise generation fails.

**Result:** Template Descriptor points to the Credential Template.

## Step 6. Replace macros

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

### Composite values (blocked)

A macro embedded inside a larger string (for example `user=${creds.get('X').username}@host`) cannot
become `$type: credRef`. Stop migration for that file. Split the value into separate parameters,
then re-run macro replacement.

**Result:** all supported macros replaced. Built-in fields still plain strings.

## Step 7. Verify and publish

Confirm that:

- every Template-owned Credential has a confirmed creation owner, `create` decision, and path
- `external_credential_template` path in the Template Descriptor is correct
- every `credId` from Step 2 that belongs in the Credential Template is present
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

Next: [Migrate Instance Repository](migrate-instance-repository.md) for the Instance Repository
consuming this Template version.

**Result:** concrete Template version published.

## Rollback

If no Environment Instance uses the new version yet - keep the previous version and fix the template.

If you published a bad version:

1. do not switch any Environment Instance to it
2. fix the Environment Template
3. publish a new concrete version

## See also

- [Overview](overview.md)
- [Migrate Instance Repository](migrate-instance-repository.md)
- [Template skill](../skills/template-repository/SKILL.md)
- [External Credentials Management](/docs/features/external-creds.md)
- [Sample external credentials template repository](/docs/samples/external-credentials/template-repository/)
