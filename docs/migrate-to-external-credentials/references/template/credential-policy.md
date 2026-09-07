# Credential creation and path policy (Template Repository)

Canonical rules for Template-owned Credentials: `create`, `remoteRefPath`.
Read **before** draft / Prepare. Analyze (inventory) may run without user decisions.

Instance-side tiers and Shared/Passport/System rules:
[../instance/credential-policy.md](../instance/credential-policy.md).
Do not copy the full Instance matrix here.

## Decision model

Record shape (narrower than Instance policy - no `creationOwner`, see below):

```text
credId: <id>
sourcePath: <path>
tier: env-tier | unknown
scope: environment | unknown
evidence: []
confidence: confirmed | proposed | ambiguous
proposedCreate: true | false | null
proposedRemoteRefPath: <path-or-null>
needsReview: true | false
```

`proposedCreate: false` is for the plan/report. Final Credential Template YAML omits `create`
when false. Never write `writeToStore` into the Credential Template (Template phase has no Store
I/O).

`create` and `remoteRefPath` are independent. Reference usage proves **shape**, not whether
`create` should be `true` or `false`.

## Template-owned Environment Credentials

Credential Template entries are `env-tier` / scope `environment` by default.

Default path proposal (only confirmed Jinja variables):

```text
{{ current_env.cloud }}/{{ current_env.name }}
```

Extra static suffix only when the user confirms a scope (for example `/db`). Never append `credId`.
EnvGene does **not** support `{{ current_env.namespace }}` in the Credential Template Jinja
context - do not use it, even as a manual override.

Default `create` proposal for Template-owned env-tier: `true` (generate a new value).

Override to `false` (keep the existing value) only with stronger evidence that the value must not
be regenerated - not merely because a marker/pattern matched (see Provider-managed below); a match
is a signal to ask, never an automatic override.

Never set `create: true` only because the Credential lives in a Credential Template.

## Ownership handoff

If a `credId` belongs to Cloud Passport or Shared at Instance time, do **not** add it to the
Credential Template only because the template references it. Record source ownership for Instance
handoff.

## Provider-managed

Same rules as Instance policy: marker/name-pattern match (known provider substrings,
e.g. `vault`, `keycloak`, plus naming patterns like a `-token` suffix or an
`idp`/`external` segment) → `confidence: ambiguous`, `needsReview: true`, null create/path. These
are signals to ask the user whether to keep the value as-is, never proof on their own. Do not
invent provider paths.

## Stop status

- Inventory without user answers is allowed.
- Status `NEEDS_INPUT` (exit `2`) when scope, create, or path is unknown/ambiguous.
- Never draft/apply ambiguous create or path. Show evidence and proposals in the report.

## Validation invariants

- No `credId` segment in `remoteRefPath`.
- No `create: true` for provider-managed without confirmation.
- Omit `create` means verify/fail-if-absent.
- Jinja path uses only `{{ current_env.cloud }}` and `{{ current_env.name }}` - not `namespace`.
- Always set `secretStore` on Credential Template entries (`default_store` unless confirmed
  otherwise). Schema default exists, but the Effective Set calculator has no runtime fallback.
- No secret values in inventory/report.
