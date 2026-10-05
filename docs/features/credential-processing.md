# Credential processing

How EnvGene populates the Environment Credentials File from multiple sources, how it decides between local and
external operating modes, and how it resolves overlaps between sources.

- [Credential processing](#credential-processing)
  - [Description](#description)
  - [Mode detection](#mode-detection)
  - [Credential sources](#credential-sources)
  - [Credential auto-generation](#credential-auto-generation)
    - [Local mode](#local-mode)
    - [External mode](#external-mode)
  - [Precedence ladder](#precedence-ladder)
  - [Merging behavior](#merging-behavior)
  - [Local-macro rewrite in external mode](#local-macro-rewrite-in-external-mode)
  - [Related documentation](#related-documentation)

## Description

The Environment Credentials File at `/environments/<cluster>/<env>/Credentials/credentials.yml` holds the
[Credential](/docs/envgene-objects.md#credential) entries used during Environment Instance generation and
consumed by the Effective Set calculator. Entries come from up to five sources that merge into a single file.
The behavior differs between **local mode** and **external mode**, which the Instance repository selects
declaratively.

For external-credential-specific concerns (external Credential object, Credential Reference syntax, VALS and
ESO rendering, external secret store provisioning) see
[External Credentials Management](/docs/features/external-creds.md).

## Mode detection

The Instance repository is in **external mode** when `/configuration/secret-stores.yml` is present. It is in
**local mode** when the file is absent. Mode is a repository-wide property. Every Environment Instance in the
same Instance repository shares the same mode.

An EnvGene template is mode-agnostic. The same template serves both local and external Instance repositories.
The template declaration of `external_credential_template` has effect only in external mode. In local mode the
field is ignored, and EnvGene emits an INFO log naming the ignored
[Credential Template](/docs/envgene-objects.md#credential-template) path.

## Credential sources

The Environment Credentials File is populated from five sources during Environment Instance generation.

| Source                          | Local mode | External mode |
|---------------------------------|------------|---------------|
| Parent Credential Template      | ignored    | applied       |
| Nested Credential Template      | ignored    | applied       |
| Auto-generated Credential       | applied    | applied       |
| Cloud Passport credentials file | applied    | applied       |
| Shared Credentials File         | applied    | applied       |

- **Parent Credential Template.** The [Credential Template](/docs/envgene-objects.md#credential-template)
  declared by a parent template in the template chain. Rendered during Environment Instance generation.
  External mode only.
- **Nested Credential Template.** The Credential Template declared by the leaf template in the template
  chain. Rendered during Environment Instance generation. External mode only.
- **Auto-generated Credential.** A Credential entry EnvGene creates for a `credId` referenced in the Instance
  but not declared by any Credential Template along the chain. The shape depends on mode. See
  [Credential auto-generation](#credential-auto-generation).
- **Cloud Passport credentials file.** The credentials file bundled with the Cloud Passport. Entries carry
  the Credential type declared when the Passport was authored.
- **[Shared Credentials File](/docs/envgene-objects.md#shared-credentials-file).** YAML files under
  `/environments/credentials/`, `/environments/<cluster>/credentials/`, or
  `/environments/<cluster>/<env>/Inventory/credentials/`, referenced from the Environment Inventory by
  `envTemplate.sharedMasterCredentialFiles`.

## Credential auto-generation

EnvGene auto-generates Credential entries for `credId` values that the Instance references but no Credential
Template declares. The shape of the generated entry depends on mode.

### Local mode

EnvGene auto-generates a **local Credential** carrying `envgeneNullValue` placeholders for every `credId`
referenced by a `${creds.get('<credId>').<field>}` macro or by a
[Built-in credential reference](/docs/features/external-creds.md#built-in-credential-references). The entry
holds placeholder values until the user replaces them. A later source that supplies a real Credential for the
same `credId` overrides the placeholder entry in the merged result.

### External mode

EnvGene auto-generates an **external Credential** for every `credId` referenced by a
[Credential Reference](/docs/features/external-creds.md#credential-reference) or
[Built-in credential reference](/docs/features/external-creds.md#built-in-credential-references) that no
Credential Template declares. The generated entry has:

```yaml
<cred-id>:
  type: external
  secretStore: default_store
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"
```

A source higher in the precedence ladder (Cloud Passport or Shared Credentials File) overrides the generated
entry.

## Precedence ladder

When the same `credId` is declared in more than one source, the entry from the higher-precedence source wins.
Precedence, lowest to highest:

1. Parent Credential Template
2. Nested Credential Template
3. Auto-generated Credential
4. Cloud Passport credentials file
5. Shared Credentials File

Shared Credentials File overrides every lower source without warning. The user is responsible for intentional
use.

Cross-source references are allowed. A Credential Reference or Built-in credential reference defined in one
source can resolve to a Credential entry contributed by another source.

## Merging behavior

How EnvGene writes the Environment Credentials File depends on mode.

**In local mode**, the Environment Credentials File persists across runs and holds user-authored values.
Sources contribute additive and override entries into the file, preserving existing user values for `credId`
entries not covered by a source.

**In external mode**, the Environment Credentials File is **regenerated on every Environment Instance
generation**. It is a derived artifact, equivalent to the rendered Cloud or Namespace files, and holds no
user-authored values. On every generation, EnvGene merges the five sources above into a single file, writing
the result once with no carryover from previous runs.

## Local-macro rewrite in external mode

In external mode, EnvGene rewrites every `${creds.get('<credId>').<field>}` macro in parameter values to a
[Credential Reference](/docs/features/external-creds.md#credential-reference) during Environment Instance
generation. The rewritten shape is:

```yaml
<parameter-key>:
  $type: credRef
  credId: <credId>
  property: <field>
```

The `property` field is omitted when the referenced Credential is single-value. The rewrite applies to
parameter values only.
[Built-in credential references](/docs/features/external-creds.md#built-in-credential-references)
such as `Cloud.defaultCredentialsId` already carry a bare `credId` and need no rewrite.

## Related documentation

- [External Credentials Management](/docs/features/external-creds.md) - external-credential object, Credential
  Reference, VALS and ESO rendering, provisioning CLI integration.
- [Credential](/docs/envgene-objects.md#credential) - Credential object schema.
- [Credential Template](/docs/envgene-objects.md#credential-template) - Credential Template object.
- [Shared Credentials File](/docs/envgene-objects.md#shared-credentials-file) - Shared Credentials File
  scopes and Jinja rendering.
- [Credential rotation](/docs/features/cred-rotation.md) - rotation flow and mode gate.
- [Credential encryption](/docs/features/credential-encryption.md) - at-rest encryption.
