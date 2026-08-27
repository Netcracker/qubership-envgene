# ADR-0001: Gate external credential provisioning with a pipeline parameter

Status: Proposed
Date: 2026-08-28

## Context

When an Environment Instance uses external Credentials, the Effective Set calculator writes the External Credential
Context and the `generate_effective_set` job invokes the External Credentials provisioning CLI to create and
validate those Credentials in the target Secret Store. Migration to external Credentials needs the context alone:
the store is not yet populated, so an unconditional provisioning call either creates empty entries or fails
validation.

## Decision

We add an optional pipeline parameter `EXTERNAL_CREDENTIAL_PROVISIONING`, an enum with values `apply` (default) and
`skip`. `apply` invokes the provisioning CLI, the current behavior. `skip` suppresses the invocation: the
calculator still writes the External Credential Context, but no Credential is created or validated and no Secret
Store is read. The value `dry-run` is reserved for a future validate-only mode. The parameter is read by the
`generate_effective_set` job, not by the calculator, whose behavior is unchanged.

Rejected:

- A field inside `EFFECTIVE_SET_CONFIG`, because the gate controls the job's provisioning step, not a Calculator
  CLI argument, so it stays a discrete pipeline parameter.
- A boolean, because "apply mode" is already the named behavior and a third mode (`dry-run`) exists, so an enum
  extends without a breaking rename.
- Reuse the provisioning CLI `--dry-run` for migration, because dry-run still authenticates to the store and
  validates presence, which migration must avoid.
- A per-Credential `create` strategy, because the choice is per-run for the whole Environment, not per-Credential.

## Consequences

- Migration obtains the External Credential Context without side effects on the Secret Store.
- The default `apply` preserves current behavior, so existing Environments are unaffected.
- The enum reserves `dry-run` for later, at the cost of a documented value that does nothing yet.
- The parameter is documentation ahead of code: the provisioning invocation is not yet wired in this repository, so
  the parameter has no consumer until that step lands and is gated on it.

See [Credential provisioning](/docs/features/external-creds.md#credential-provisioning) and
[`EXTERNAL_CREDENTIAL_PROVISIONING`](/docs/instance-pipeline-parameters.md#external_credential_provisioning).
