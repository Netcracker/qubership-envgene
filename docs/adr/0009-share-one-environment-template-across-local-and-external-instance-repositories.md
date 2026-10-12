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

- **Mode signal.** The Instance repository is in external mode when `/configuration/secret-stores.yml` is
  present, local mode otherwise; the mode is repository-wide. Chosen over a boolean flag (the file is
  already required for external operation) and over Credential Template presence (which would couple mode to
  template authoring).
- **Credential Template optional, with auto-generation.** The Credential Template is optional, and EnvGene
  auto-generates an external Credential for any referenced `credId` that no source provides, so a template
  needs to declare only the credentials it wants to shape. In local mode the Credential Template is ignored.
- **Fixed precedence ladder.** Credential sources merge in a fixed order with the Shared Credentials File
  highest, so a synthesized default never shadows discovered data and an explicit operator choice always
  wins.
- **Derived credentials file in external mode.** The Environment Credentials File is regenerated on every
  run in external mode (it holds only references, not user values); local keeps merge-preserve.
- **Unified parameter notation.** Template authors write only `${creds.get(...)}`; external mode rewrites it
  to a Credential Reference, so one notation serves both modes.
- **Jinja rendering of the Shared Credentials File.** The file is rendered regardless of extension, by the
  same mechanism as the Credential Template; the `.j2` suffix is linter hygiene only.
- **Credential rotation scoped to local mode.** Credential rotation runs only in local mode; in external
  mode the rotation step fails at entry and directs the operator to the Secret Store's own rotation
  mechanism.
- **External-mode credential restrictions.** In external mode `vaultAppRole` Credentials are not
  externalizable, sensitive parameter values must be whole-value references (no literal text, no second
  reference), and the deprecated `#creds` / `#credscl` / `#credsns` macros are unsupported. Each fails
  Environment Instance generation; local mode permits all three.

Rejected:

- Fork into a separate template per mode, because operators maintain duplicate chains and divergence
  between modes becomes an ongoing liability.
- Convert the shared template to external-only on introduction of external support, because every local
  instance repository then migrates in lock-step, which is the problem this decision avoids.
- Keep mode as a template-chain property set by `external_credential_template` declaration (previous
  behavior), because it couples mode to template authoring and prevents one template from serving
  different modes.
- Gate Shared Credentials File rendering on a `.yml.j2` suffix (opt-in), because external shared
  Credentials almost always need Jinja in `remoteRefPath`, so a forgotten suffix silently yields an
  unrendered, invalid reference — and the suffix carries no benefit here (the rendered output is written
  to a separate file, so there is no source self-overwrite; instance repositories are not linted).

## Consequences

- One Environment Template serves many instance repositories in mixed modes with no coordinated
  migration.
- Creating `/configuration/secret-stores.yml` in a repository with prior local Credential entries
  discards those entries on the next Environment Instance generation. Recovery requires Git history.
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
