# Design

## Approaches

- **A. Fallback branch in the env config template (recommended).** The cluster block of the environment
  configuration template already derives the four `current_env.cluster` connection macros from `clusterUrl`. Add one
  `elif` branch that derives them from the render-context Cloud Passport when `clusterUrl` is not set, and keep the
  existing empty-string `else`. The derivation stays in the one place that already owns it.
- **B. Resolve in the Python render context.** Compute the four values in the generator before rendering and inject
  them. Trade-off: splits the cluster derivation across the template (for `clusterUrl`) and Python (for the passport),
  so a reader has to look in two places for one behavior. Rejected as not surgical.
- **C. Fill from the Cloud Passport processing module.** Extend the module that writes `cloud.yml`. Trade-off: that
  module owns the `cloud.yml` deploy parameters, not the `current_env.cluster` context, and it mutates a separate
  passport copy. Coupling the cluster context to it is the wrong seam. Rejected.

## Decision

Approach A, accepted by popoveugene in chat across this design discussion. Precedence is fallback, not override:
`clusterUrl` stays the source whenever it is set. The passport protocol value is normalized with upper-case to match
the `clusterUrl` path, and each field uses a default of empty string so a passport that omits a value yields an empty
macro rather than an error.

## Contracts

- C-1 | consumes | the render context exposes a top-level `cloud_passport` loaded fresh from the Cloud Passport file,
  carrying `cloud.CLOUD_PROTOCOL`, `cloud.CLOUD_API_HOST`, `cloud.CLOUD_API_PORT`, and `cloud.CLOUD_PUBLIC_HOST`. This
  load is independent of the copy consumed when writing `cloud.yml`, so all four keys are present at render. The
  decision reads these four keys in the fallback branch.
- C-2 | provides | `current_env.cluster.cloud_api_protocol`, `cloud_api_url`, `cloud_api_port`, and `cloud_public_url`
  resolve to the `clusterUrl`-derived values when `clusterUrl` is set, otherwise to the matching passport values,
  otherwise to empty strings. A missing passport key yields an empty string for that macro only.
- C-3 | preserves | when `clusterUrl` is set the existing derivation is unchanged and the Cloud Passport is not
  consulted for these macros.

## Order and Dependencies

None. Single component, no cross-component merge order.

## Constraints

- Simplicity: add only the one fallback branch. No new parameter, no abstraction, no handling for cases the specs do
  not name.
- Surgical: touch only the cluster block and the four macro entries in the template-macros doc. Do not reformat or
  improve the surrounding template.
- Match existing style: mirror the `clusterUrl` branch's Jinja form and indentation in the new branch.
- Test the real thing: the tests drive the real environment configuration generation, never a reimplementation of the
  resolution rules.
- No comments or docstrings in new code or tests. Name values for what they are.

## Out of Scope

- `cloud.yml` generation and the `cloud_passport` context block, both unchanged.
- The `current_env.cloud_passport.cloud.CLOUD_PUBLIC_HOST` macro, which keeps working as before.
- Passport fields other than the four cluster connection values (private url, dashboard, credentials, and the rest).
- Override precedence, where the passport would win over a set `clusterUrl`. Rejected in favor of fallback.

## Open Questions

None. The key-presence question is settled by C-1, and the protocol casing is decided in the Decision.
