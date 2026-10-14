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
  - [External-mode credential restrictions](#external-mode-credential-restrictions)
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

EnvGene auto-generates Credential entries for `credId` values that the Instance references but **no source
provides** — neither a Credential Template, the Cloud Passport credentials, nor a Shared Credentials File.
Auto-generation is the last-resort gap filler: its entry is the final one only where no source supplies the
`credId`. The shape of the generated entry depends on mode.

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
source provides (no Credential Template, Cloud Passport, or Shared Credentials File). The generated entry has:

```yaml
<cred-id>:
  type: external
  secretStore: default_store
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"
```

Auto-generation has the lowest effective priority in the [precedence ladder](#precedence-ladder): any source
(a Credential Template, the Cloud Passport, or a Shared Credentials File) that supplies the same `credId`
wins, so a generated entry survives only where no source provides the `credId`. Whether EnvGene generates
the entry before or after the other sources is an implementation detail; the result is the same.

## Precedence ladder

When the same `credId` is declared in more than one source, the entry from the higher-precedence source wins.
Precedence, lowest to highest:

1. Auto-generated Credential
2. Parent Credential Template
3. Nested Credential Template
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

## External-mode credential restrictions

Three restrictions apply in external mode. Each one fails Environment Instance generation with an explicit
error. In local mode the same inputs are permitted (they resolve inline to plain text, or, for deprecated
macros, keep working).

### `vaultAppRole` cannot be externalized

A `vaultAppRole` Credential is the AppRole authentication identity (`roleId`, `secretId`, `path`,
`namespace`) that an application uses to log in to HashiCorp Vault and fetch its other secrets. It is the
bootstrap access to the Secret Store itself, so it cannot be stored as an external reference: resolving that
reference would already require the Vault access the Credential provides (a circular dependency). The
external Credential shape (`secretStore`, `remoteRefPath`, `properties` limited to `username`/`password`) has
no place for its fields.

When a `vaultAppRole` Credential is referenced (through a `${creds.get('<id>').roleId}` / `.secretId` macro
or a Credential declaration), generation fails with an error naming the `credId`. EnvGene does not silently
drop it or coerce it to another type. Provide Secret Store access (the AppRole login) to the pipeline through
environment or CI configuration, not as a Credential in the Environment Credentials File.

### Whole-value credential reference only

A sensitive parameter value that references an external Credential must consist of exactly one reference
occupying the entire value. A credential reference cannot be combined with literal text or with a second
reference. This applies to string values in `deployParameters` and `e2eParameters` that contain a
`${creds.get('<credId>').<field>}` macro. A structured
[Credential Reference](/docs/features/external-creds.md#credential-reference) (`$type: credRef`) is an object
that already occupies the whole value, so it is never affected.

Formally, for a string value `V` containing one or more credential macros, let `refs(V)` be those macros.
`V` is valid only when both hold:

1. `len(refs(V)) == 1` (exactly one reference), and
2. `V` trimmed equals that reference (no literal characters before or after).

Two violation cases fail generation:

- **multiple:** two or more references, for example `oracle://${creds.get('db').username}:${creds.get('db').password}@host:1521/SID`.
- **embedded:** one reference plus literal text, for example `https://${creds.get('svc').username}@host`.

Neither the VALS nor the ESO delivery flow can represent such a value, so there is no external rendering for
it. The error names the parameter key, the `credId` or credIds, and the case. Move the reference into a
dedicated parameter so the application or Helm chart composes the final string.

### Deprecated key-form macros

The deprecated key-form credential macros `#creds{<credId>, <field>}`, `#credscl{...}`, and `#credsns{...}`
(the macro is the parameter key; the value is the `credId`) are not supported in external mode. A referenced
one fails generation with an error naming the parameter key and the `credId`, advising replacement with
`${creds.get('<credId>').username}` / `.password` / `.secret` or a
[Credential Reference](/docs/features/external-creds.md#credential-reference). These macros are deprecated;
see [Deprecated Credential Macros](/docs/template-macros.md#deprecated-credential-macros). Migration to
external converts them to `credRef` on apply, so this check is a backstop for an incomplete conversion.

## Related documentation

- [External Credentials Management](/docs/features/external-creds.md) - external-credential object, Credential
  Reference, VALS and ESO rendering, provisioning CLI integration.
- [Credential](/docs/envgene-objects.md#credential) - Credential object schema.
- [Credential Template](/docs/envgene-objects.md#credential-template) - Credential Template object.
- [Shared Credentials File](/docs/envgene-objects.md#shared-credentials-file) - Shared Credentials File
  scopes and Jinja rendering.
- [Credential rotation](/docs/features/cred-rotation.md) - rotation flow and mode gate.
- [Credential encryption](/docs/features/credential-encryption.md) - at-rest encryption.
