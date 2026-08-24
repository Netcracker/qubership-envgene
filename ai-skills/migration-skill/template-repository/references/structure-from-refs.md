# Structure from references

Policy: [credential-policy.md](credential-policy.md).

Collect **evidence** for shape and ownership proposals. Do not treat heuristics as confirmation.

| Evidence | Shape proposal |
|----------|----------------|
| `.username` / `.password`, or `#creds*` key | multi-field |
| `.secret` | single-value |
| `maasConfig.credentialsId` / `dbaasConfigs[].credentialsId` | multi-field |
| `vaultConfig.credentialsId` / `consulConfig.tokenSecret` | single-value |
| `Namespace.credentialsId` / `Tenant.credential` | single-value |
| `Cloud.defaultCredentialsId` only | unknown shape - ask |
| Same `credId` as both shapes | conflict - ask |

Reference usage does **not** prove `creationOwner`. Emit proposals (`proposedCreate`,
`proposedRemoteRefPath`) with `confidence: proposed` or `ambiguous` and `needsReview: true` until
the user confirms.

Heuristic provider markers → `creationOwner: unknown`, null create/path, review.

Skip macros in `technicalConfigurationParameters`.
