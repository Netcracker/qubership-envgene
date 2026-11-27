# Migrate a template repository to external Credentials

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Step 1: Create the Credential Template](#step-1-create-the-credential-template)
- [Step 2: Describe the credentials of the template](#step-2-describe-the-credentials-of-the-template)
- [Step 3: Replace the credential macros](#step-3-replace-the-credential-macros)
- [Step 4: Check and publish the template](#step-4-check-and-publish-the-template)
- [Rollback](#rollback)
- [See also](#see-also)

## Description

Move an Environment Template to external Credentials. At the end, the template describes its credentials in a
Credential Template and is published as a new version. Repeat the steps for each Template Descriptor.

Only the template files change. The secret values move to the Secret Store during
[Migrate an instance repository to external Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md).

## Prerequisites

- Every environment that uses this template is on a No-CMDB
  [deployment architecture](/docs/deployment-architecture.md). CMDB import does not work with external Credentials.
- You know the Secret Store identifier that the Instance repositories use. Skip this if they use `default_store`.

## Step 1: Create the Credential Template

1. Create the file `templates/env_templates/external-cred/<template-name>.yml.j2`, one per Template Descriptor.
2. In the Template Descriptor, add `external_credential_template` with the path to this file:

    ```yaml
    # templates/env_templates/external-cred-sample.yml
    tenant: "{{ templates_dir }}/env_templates/external-cred/tenant.yml.j2"
    cloud: "{{ templates_dir }}/env_templates/external-cred/cloud.yml.j2"
    external_credential_template: "{{ templates_dir }}/env_templates/external-cred/external-credentials.yml.j2"
    namespaces:
      - template_path: "{{ templates_dir }}/env_templates/external-cred/ns.yml.j2"
    ```

## Step 2: Describe the credentials of the template

Open the files of the Template Descriptor:

1. The files in `tenant`, `cloud`, and every `namespaces[].template_path`.
2. The ParameterSets listed in `deployParameterSets`, `e2eParameterSets`, and `technicalConfigurationParameterSets`
   of these files: `templates/parameters/<name>.yml` or `<name>.yml.j2`.

If the descriptor has `parent-templates`, also describe the credentials of the built-in fields of the parent
templates.

For each credential reference in these files, add an entry to the Credential Template. The key of the entry is the
`credId` of the reference:

| Reference                  | Example                                  | `credId`         |
|----------------------------|------------------------------------------|------------------|
| Macro in a parameter value | `${creds.get('app-db-cred').username}`   | `app-db-cred`    |
| Key-form macro             | `'#creds{LOGIN, PASSWORD}': app-db-cred` | `app-db-cred`    |
| Built-in field             | `credentialsId: ns-deploy-cred`          | `ns-deploy-cred` |

- Macros include `envgen.creds.get` and `cmdb.creds.get`.
- For `#credscl` and `#credsns`, the `credId` is not the value of the key. Copy it from `Credentials/credentials.yml`
  of an environment built from this template.
- The full list of built-in fields is in
  [Built-in credential references](/docs/features/external-creds.md#built-in-credential-references).

Set the fields of each entry:

| Field           | Value                                                                                                                                                                                                                      |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `type`          | Always `external`                                                                                                                                                                                                          |
| `secretStore`   | The identifier of the Secret Store of the Instance repositories                                                                                                                                                            |
| `remoteRefPath` | The folder in the store, for example `{{ current_env.cluster.name }}/{{ current_env.name }}`. Do not add the `credId`: EnvGene appends it. See [Credential Template](/docs/features/external-creds.md#credential-template) |
| `create`        | Leave it out if any environment holds a real value. `true` if the environments hold only `envgeneNullValue`                                                                                                                |
| `properties`    | `- name: username` and `- name: password` for a username and password pair. Leave it out for one value                                                                                                                     |

A username and password pair is a macro with `.username` or `.password`, or a key-form macro. One value is a macro
with `.secret`. For a built-in field, take the `type` of the credential from `Credentials/credentials.yml` of an
environment: `usernamePassword` is a pair, `secret` is one value.

```yaml
# templates/env_templates/external-cred/<template-name>.yml.j2
app-db-cred:                # a pair, the environments hold the value
  type: external
  secretStore: default_store
  remoteRefPath: "{{ current_env.cluster.name }}/{{ current_env.name }}"
  properties:
    - name: username
    - name: password
app-sidecar-token:          # one value, EnvGene generates it
  type: external
  create: true
  secretStore: default_store
  remoteRefPath: "{{ current_env.cluster.name }}/{{ current_env.name }}"
ns-deploy-cred:             # held by credentialsId of a Namespace
  type: external
  secretStore: default_store
  remoteRefPath: "{{ current_env.cluster.name }}/{{ current_env.name }}"
```

> [!WARNING]
> Do not set `create: true` for a credential that has a real value. EnvGene generates a new value, and the existing
> password, token, or key is lost.

## Step 3: Replace the credential macros

In the files from Step 2, replace each credential macro with `$type: credRef`. Leave built-in fields unchanged: they
keep a plain `credId`.

Do not change the files of a parent template from another repository. EnvGene rewrites their macros when it
generates the Environment Instance.

| Macro                                                                    | Replace with                                                                    |
|--------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| `${creds.get('<credId>').username}`, `${creds.get('<credId>').password}` | `$type: credRef` with `credId: <credId>` and `property: username` or `password` |
| `${creds.get('<credId>').secret}`                                        | `$type: credRef` with `credId: <credId>`, without `property`                    |
| `'#creds{LOGIN, PASSWORD}': <credId>`, `#credscl{...}`, `#credsns{...}`  | Two `$type: credRef` entries, `LOGIN` and `PASSWORD`                            |

`envgen.creds.get` and `cmdb.creds.get` are replaced the same way as `creds.get`.

```yaml
# Before
DB_USER: "${creds.get('app-db-cred').username}"
'#creds{LOGIN, PASSWORD}': app-db-cred

# After
DB_USER:
  $type: credRef
  credId: app-db-cred
  property: username
LOGIN:
  $type: credRef
  credId: app-db-cred
  property: username
PASSWORD:
  $type: credRef
  credId: app-db-cred
  property: password
```

Some macros cannot be replaced as they are:

- A macro that is part of a longer value, such as `https://${creds.get('svc').username}@host`. Move the macro to a
  separate parameter.
- A credential macro in `technicalConfigurationParameters`. External Credentials do not work there. Agree with the
  template owner how to handle the parameter.
- A credential of type `vaultAppRole`. It cannot be external. Remove the reference and agree with the template owner
  how the application gets access to Vault.

## Step 4: Check and publish the template

1. Check that:
    - `external_credential_template` points to the file from Step 1
    - every credential reference from Step 2 has an entry in the Credential Template
    - no credential macros are left in the files from Step 2
2. Run the template build pipeline and publish a new version, for example `project-env-template:2.0.0`.

Next, migrate each Instance repository that uses this template, see
[Migrate an instance repository to external Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md).

## Rollback

If no Environment Instance uses the new version yet, keep the previous version and fix the template.

If you published a bad version:

1. Do not switch any Environment Instance to it.
2. Fix the Environment Template.
3. Publish a new version.

## See also

- [Migrate an instance repository to external Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md)
- [Configure external Credentials](/docs/how-to/configure-external-credentials.md)
- [Built-in credential references](/docs/features/external-creds.md#built-in-credential-references)
- [Credential Template](/docs/envgene-objects.md#credential-template)
- [Template Descriptor](/docs/envgene-objects.md#template-descriptor)
