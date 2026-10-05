# ADR-0009: Share one Environment Template across local and external instance repositories

Status: Proposed

## Context

A shared Environment Template can serves many instance repositories. Introducing external secret-store
support must not force every instance repository that uses a given template to migrate at once. The same
parent template must continue to serve local instance repositories while supporting external ones. Previous
behavior inferred mode from the Template Descriptor `external_credential_template` field, which couples
mode to template authoring and blocks mixed use.

## Decision

One Environment Template serves instance repositories in either mode. The instance repository selects its
mode by a local signal. The template remains mode-agnostic. In external mode, the Environment Credentials
File is a derived output assembled on every run from a fixed set of sources, with no mandatory template-side
authoring. The design is wired through the following mechanisms:

- **Mode signal.** The instance repository is in external mode when `/configuration/secret-stores.yml` is
  present, local mode otherwise. Mode is repository-wide. Every Environment Instance in the repository
  shares the mode.
- **Mode-agnostic Credential Template.** The Credential Template is optional. In external mode, EnvGene
  auto-generates an external Credential (`type: external`, `secretStore: default_store`, default
  `remoteRefPath`) for every `credId` not declared by any Credential Template in the chain. In local mode
  the Credential Template is ignored, even when declared, and an INFO log names the ignored file.
- **Fixed precedence ladder.** Credential sources merge in a fixed order, lowest to highest: parent
  Credential Template, nested Credential Template, auto-generated Credential, Cloud Passport credentials
  file, Shared Credentials File. A higher source wins on `credId` overlap. The Shared Credentials File
  silently overrides every lower source.
- **Derived credentials file in external mode.** In external mode, the Environment Credentials File is
  regenerated on every Environment Instance generation. The step assembles the ladder sources in memory
  and writes the file once, replacing any existing content. In local mode the file persists across runs
  with merge-preserve.
- **Unified parameter notation.** In external mode, EnvGene rewrites every `${creds.get('<id>').<field>}`
  macro in parameter values to a Credential Reference (`$type: credRef`) during Environment Instance
  generation. Template authors use the local macro notation only. Built-in credential references, which
  already carry a bare `credId`, are not rewritten.
- **Jinja opt-in for the Shared Credentials File.** A Shared Credentials File with the `.yml.j2` or
  `.yaml.j2` suffix is rendered as a Jinja template with the environment context before merging. A file
  without the suffix is read verbatim.
- **Credential rotation scoped to local mode.** Credential rotation runs only in local mode. In external
  mode, the rotation step fails at entry with one error directing the operator to the Secret Store's
  rotation mechanism. No per-credential processing happens.

Rejected:

- Fork into a separate template per mode, because operators maintain duplicate chains and divergence
  between modes becomes an ongoing liability.
- Convert the shared template to external-only on introduction of external support, because every local
  instance repository then migrates in lock-step, which is the problem this decision avoids.
- Keep mode as a template-chain property set by `external_credential_template` declaration (previous
  behavior), because it couples mode to template authoring and prevents one template from serving
  different modes.

## Consequences

- One Environment Template serves many instance repositories in mixed modes with no coordinated
  migration.
- Creating `/configuration/secret-stores.yml` in a repository with prior local Credential entries
  discards those entries on the next Environment Instance generation. Recovery requires git history.
- Operators cannot hand-author one-off external Credential entries in the Environment Credentials File.
  Overrides flow through the Shared Credentials File or the Cloud Passport.
- The Shared Credentials File silently overrides every lower source. The operator accepts responsibility
  for intentional use.
- Debugging an external parameter reads the rewritten Credential Reference, not the local macro the
  template declared. Readers reconcile the rendered output against the template source.
- Operators of external instance repositories rotate credential values through the Secret Store's own
  tooling, not through EnvGene.

Supersedes implicit mode detection via Template Descriptor `external_credential_template` presence.

See [Credential processing](/docs/features/credential-processing.md) for observable behavior and
[External Credentials Management](/docs/features/external-creds.md) for external-specific objects.
