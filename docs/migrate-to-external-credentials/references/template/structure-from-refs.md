# Structure from references

Policy: [credential-policy.md](credential-policy.md).

Collect **evidence** for shape and `create` proposals. Do not treat heuristics as confirmation.

| Evidence | Shape proposal |
|----------|----------------|
| `.username` / `.password`, or `#creds*` key | multi-field |
| `.secret` | single-value |
| `maasConfig.credentialsId` / `dbaasConfigs[].credentialsId` | multi-field |
| `vaultConfig.credentialsId` / `consulConfig.tokenSecret` | single-value |
| `Namespace.credentialsId` / `Tenant.credential` | single-value |
| `Cloud.defaultCredentialsId` only | unknown shape - ask |
| Same `credId` as both shapes | conflict - ask |

Reference usage does **not** prove whether `create` should be `true` or `false`. Emit
proposals (`proposedCreate`, `proposedRemoteRefPath`) with `confidence: proposed` or
`ambiguous` and `needsReview: true` until the user confirms.

Heuristic provider markers/name patterns → `confidence: ambiguous`, null create/path, review.

Skip macros in `technicalConfigurationParameters`.
