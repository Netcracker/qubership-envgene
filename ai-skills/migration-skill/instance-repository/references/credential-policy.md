# Credential creation and path policy (Instance Repository)

Canonical rules for `create`, `remoteRefPath`, creation owner, and tiers during Instance
migration. Read **before** Prepare / convert / apply. Analyze may run without user decisions.

Full decision model (shared concepts): see also Template
[credential-policy.md](../../template-repository/references/credential-policy.md) for Template-owned
defaults. Do not duplicate this matrix in other Instance references - link here instead.

## Decision model

Determine `create` and `remoteRefPath` independently:

- `create` depends on who must create the value and whether generating a new value is allowed.
- `remoteRefPath` depends on the Credential's actual scope.
- Source file location gives tier and a default proposal. Stronger evidence overrides the proposal
  only after confirmation. Do not auto-reclassify on weak signals.
- `credId` and comments are not sufficient proof.

Decision record (every Credential):

```text
credId: <id>
sourcePath: <path>
tier: passport-tier | env-tier | external-tier | unknown
scope: cluster | environment | shared | system | provider | unknown
creationOwner: envgene | pre-existing | provider | unknown
evidence: []
confidence: confirmed | proposed | ambiguous
proposedCreate: true | false | null
proposedRemoteRefPath: <path-or-null>
needsReview: true | false
```

`proposedCreate: false` belongs in the migration plan and report. In final External Credential YAML
omit the `create` field (do not write `create: false`).

`writeToStore` is migration-plan only (transfer plaintext to Store). Never add it to final YAML.
Skills/scripts in this folder do not perform Store I/O - they only record the operator choice.

## Evidence priority

Apply top-down:

1. Explicit user decision, approved mapping, or repository metadata.
2. Explicit provisioning/ownership declaration in project config or docs.
3. Actual source path and binding to Cloud Passport / Environment / Shared file.
4. Actual usage scope from `env_definition.yml`, Descriptor, and references.
5. `credId`, comments, service markers - heuristic only.

If levels 1-4 conflict: `confidence: ambiguous`, `needsReview: true`, do not convert.

## Tier from Instance sources

| Source | Tier | Default scope |
|--------|------|---------------|
| Cloud Passport Credentials | `passport-tier` | `cluster` |
| Environment-level Shared (`.../<env>/Inventory/credentials/`) | `env-tier` | `environment` |
| Repository-level Shared (`environments/credentials/`) | `external-tier` | `shared` |
| Cluster-level Shared (`environments/<cluster>/shared-credentials/` or `<cluster>/credentials/`) | `external-tier` | `shared` |
| System Credentials | `external-tier` | `system` |
| Unknown / conflicting | `unknown` | `unknown` |

Source location sets the default proposal. If usage proves another scope, record a conflict and ask.
Do not silently change tier.

## Creation owner and create

| Owner | Meaning |
|-------|---------|
| `envgene` | EnvGene may generate a new value when the secret is absent |
| `pre-existing` | Secret must exist (or be transferred) before use |
| `provider` | External service / operator / platform / SaaS creates the value |
| `unknown` | Insufficient or conflicting evidence |

Tier default proposals (not final):

| Tier | Default owner | Default create |
|------|---------------|----------------|
| `passport-tier` | `pre-existing` | `false` |
| `env-tier` | `envgene` | `true` |
| `external-tier` | `pre-existing` | `false` |
| `unknown` | `unknown` | `null` |

Override when stronger evidence exists (existing value must be kept → `pre-existing`/`false`;
provider creates → `provider`/`false`; generation explicitly allowed → `envgene`/`true`;
unknown → `unknown`/`null` + review).

| Creation owner | Migration plan | Final YAML |
|----------------|----------------|------------|
| `envgene` | `create: true` | `create: true` |
| `pre-existing` | `create: false` | omit `create` |
| `provider` | `create: false` | omit `create` |
| `unknown` | do not set | do not change Credential |

Never set `create: true` for System Credentials, confirmed provider-managed Credentials, when the
current value must be kept, or without confirmation that generation is allowed.

## remoteRefPath

Prefix only. EnvGene appends normalised `credId`. Never include `credId` in the path.

| Scope | Default path | Example |
|-------|--------------|---------|
| cluster / Cloud Passport | `<cluster>` | `prod-cluster` |
| environment | `<cluster>/<environment>` | `prod-cluster/env-a` |
| environment + confirmed scope | `<cluster>/<environment>/<scope>` | `prod-cluster/env-a/bss` |
| shared cross-scope | `external` or approved shared path | `external` |
| system | approved system path; fallback `external` | `external/envgene` |
| provider | confirmed provider path | `prod-cluster/dbaas` |
| unknown | do not set | — |

Do not add a leading `/` unless the project's Secret Store convention already uses it. Keep one
format inside the repository.

## Provider-managed

Confirming evidence: explicit mapping, metadata, documented flow, or user/Platform confirmation.

Heuristic markers (`consul`, `dbaas`, `argocd`, `webex`, `operator`, `service-account`, comments
like "managed"/"external", multi-env use, appears after platform install) → only:

```text
creationOwner: unknown
confidence: ambiguous
needsReview: true
proposedCreate: null
proposedRemoteRefPath: null
```

Do not set `create: true`, auto-pick a provider path, or remove `data`. Ask for owner, store path,
and when the secret appears in the Store.

After confirmed `provider`: `proposedCreate: false`, confirmed path, `confidence: confirmed`,
`needsReview: false`. Do not finish cutover until secret availability in the Store is confirmed.

## Instance source rules

### Cloud Passport

- `tier: passport-tier`; path proposal `<cluster>`; create proposal `false`.
- `true` only with explicit confirmation of EnvGene generation.

### Environment-level Shared

- `tier: env-tier`; path `<cluster>/<environment>`; create proposal `true`.
- Keep existing value → `false` + `writeToStore: true` in the plan.
- Unknown owner → review.

### Repository / cluster-level Shared

- `tier: external-tier`; path `external` or approved shared path; create proposal `false`.
- Not the same as Cloud Passport unless confirmed.

### System Credentials

- `tier: external-tier`; create always `false` / omit; path approved system path (fallback
  `external`); transfer before removing `data`; Vault/GCP only per How-to.

### Template-dependent Credentials

Use Template handoff decisions. Do not recalculate create/path in Instance without new evidence.
Handoff vs Instance conflict → review.

## Stop status

- Analyze without user answers is allowed.
- Status `NEEDS_INPUT` (script exit `2`) when creation owner, scope, or required path is unknown /
  ambiguous, or `needsReview: true`.
- Never apply an ambiguous proposal. Show evidence and proposed values in the report.

## Validation invariants

- Applied entries have known tier, scope, creation owner, and path.
- `needsReview: true` or `confidence: ambiguous` blocks convert/apply for that Credential.
- `remoteRefPath` must not end with or contain `credId` as a segment.
- System and provider-managed must not have `create: true`.
- `create: true` requires evidence that a new value is allowed.
- Omit `create` in YAML means verify/fail-if-absent, not generation.
- No `writeToStore` in final YAML. No secret values in inventory/report.
- Remove `data` only after confirmed transfer/provisioning.
