# Open questions for migration to External Credentials

- [How to decide `create`](#how-to-decide-create)
- [How to decide `remoteRefPath`](#how-to-decide-remoterefpath)
- [Who creates Credentials in the external store](#who-creates-credentials-in-the-external-store)
- [How to migrate a shared Template](#how-to-migrate-a-shared-template)
- [Is support for multiple Secret Stores required](#is-support-for-multiple-secret-stores-required)
- [How to handle complex Credential usage](#how-to-handle-complex-credential-usage)
- [What to verify after migration](#what-to-verify-after-migration)
- [Related documentation](#related-documentation)

## How to decide `create`

There is no rule yet that decides when:

- EnvGene must create the Credential
- the Credential already exists in the external store
- the project team must create the Credential

A decision is needed for how operators and migration tooling set `create` on each External Credential.

## How to decide `remoteRefPath`

A decision is needed for whether to:

- use the path of an already existing secret
- use a path formed by EnvGene
- leave path authorship to a specific role (operator, project team, or EnvGene)

The decision must also say who is responsible for setting `remoteRefPath` during migration.

## Who creates Credentials in the external store

A decision is needed for:

- what EnvGene creates
- what the project team creates
- whether building a list of Credentials to create is enough for the migration process

Until this is settled, migration guides can only state that value preparation in the external store is a
separate process. They cannot define ownership or completion criteria for that process.

## How to migrate a shared Template

There is no defined process for a Template used by several Instance Repositories that cannot migrate at the
same time.

It is also unclear how to migrate parent and child Templates when some consumers still use local Credentials.

A decision is needed for:

- staged cutover across Instance Repositories that share one Template
- coexistence of External Credentials and local Credentials across parent and child Templates
- versioning or branching rules during the transition

## Is support for multiple Secret Stores required

If multiple Secret Stores are in scope, a decision is needed for who defines the mapping:

`credId` → Secret Store

If a single Secret Store is enough for migration, that limit should be stated explicitly so tooling and
guides do not invent per-Credential store selection rules.

## How to handle complex Credential usage

A decision is needed for behaviour when:

- one `credId` is used in different parameter types
- a Credential is used in `technicalConfigurationParameters`
- the Credential type or structure differs between the Template and the Instance Repository

Each case needs a clear outcome: migrate as one External Credential, split into separate Credentials, fail
validation, or leave as an exception.

## What to verify after migration

A decision is needed for:

- whether a successful Environment Instance generation is enough
- what to check in the Effective Set
- whether a test deployment is required
- which errors block migration completion

The Instance Repository how-to already describes TEMPORARY smoke, Effective Set checks, test deployment, and
PERSISTENT cutover. This question asks which of those checks are mandatory exit criteria versus optional
confidence checks.

## Related documentation

| Document                                                                                                                         | Role                                      |
|----------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------|
| [External Credentials](/docs/features/external-creds.md)                                                                         | Feature reference                         |
| [Migrate Template Repository to External Credentials](/docs/how-to/migrate-template-repository-to-external-credentials.md)       | Template Repository migration how-to      |
| [Migrate Instance Repository to External Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md)       | Instance Repository migration how-to      |
| [External Credentials Provisioning CLI](/docs/features/external-creds-provisioning-cli.md)                                       | Provisioning CLI reference                |
