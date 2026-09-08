# ADR-0006: Resolve resource profile baseline and override by signal-gated side selection

Status: Accepted

## Context

When generating the effective set, the resource profile for an application is resolved from two possible
sides, the namespace and the cloud. Today the active side is chosen by testing only whether the namespace
object baseline is set. A namespace that carries only an override, with no object baseline, is therefore
discarded silently and the cloud side is used instead.

Within the chosen side the override is applied only when a baseline of the resolved name is found in the
service. An application that has an override but no matching baseline receives neither baseline parameters
nor its override, and no error is raised. When an override is present its own baseline is the effective
selector, yet in the default merge mode the merged override keeps the template baseline and silently drops
an environment-specific baseline.

The namespace object restricts baseline to a fixed set of allowed values, while the override object allows
any value, and the cloud object has no profile at all. A standalone environment-specific override, one that
has no matching profile reference on the cloud or namespace template, is rejected with a hard error, which
blocks use cases that need no template profile. The user-facing documentation also contradicts the actual
behavior, describing the override baseline as unused and the selection as happening at the cloud or
namespace level.

## Decision

We replace the object-baseline-only gate with a signal gate. A namespace is the active side if it has any
profile signal, meaning its object baseline is set or an override is present for it. Otherwise the cloud is
the active side. The namespace is the recommended layer for setting a resource profile. The cloud profile
is a rarely-needed fallback.

Within the active side, baseline precedence is: the environment-specific override's baseline, then the
template override's baseline, then the object baseline. Replace mode drops the template override, so the
precedence collapses to environment-specific override baseline then object baseline. Changing the baseline
for an environment is done with replace mode. Replace drops the template override, so parameters bound to
the old baseline are not carried onto the new one. Merge mode is for adding parameters on the same baseline,
and merging a different baseline is the warned wrong path.

The override is always applied. Baseline parameters are layered under it only when the resolved name is
found among a service's baselines. No hard failures are introduced. The calculator and the environment
build step emit warnings for abnormal-but-tolerated cases:

- A baseline name is specified but absent from a service that does ship baselines.
- Merge mode where the template override carries parameters and its baseline differs from the
  environment-specific override's baseline.
- A parameter-carrying override that declares no baseline.

A service that ships no baselines at all is not warned.

Override parameters are conceptually bound to a baseline. This is upheld by guidance and warnings, not by
a hard failure. A standalone environment-specific override is allowed. Merge preserves the
environment-specific baseline.

An empty-string baseline is treated as absent everywhere in the resolution logic. Source files are not
rewritten. An empty string is marked as bad practice in the configuration standard.

Schema rules:

- Baseline is a free-form string in all object schemas (the fixed enumeration is dropped).
- Baseline stays optional in the schema so existing configurations keep loading.
- Setting a baseline is mandated by configuration best practice, not by the schema.
- The cloud object gains an optional profile with a name and a free-form baseline for schema completeness.
- The parameter list is optional. An override may set only a baseline, with no parameters, to change the
  baseline without any parameter overrides.

Rejected:

- Cloud-plus-namespace layering, where the cloud override would be a base and the namespace override would
  apply on top, because no existing environment uses both levels at once and the added complexity risks
  changing today's non-empty outputs with no observed benefit.
- A materialized default baseline for namespaces that have a profile but omit a baseline, because a broad
  default would silently inject a baseline into profile-less namespace objects that have none today.
- A hard failure when the resolved baseline name is absent from a service's baselines, because the
  name-not-found case cannot be bounded without inspecting each application's baselines at generation
  time, the check would be doc-ahead of code, and a schema-required baseline would break existing
  configurations. Warnings are used instead.
- CMDB-style baseline-as-binding with a hard fail on override-baseline-versus-effective-baseline
  mismatch, because the dangerous case (parameters intended for one baseline applied under a different
  effective baseline) is absent from the corpus, hard fail is doc-ahead and BC-risky, and schema-required
  baseline would break existing configurations. Warnings and best-practice documentation are used instead.

## Consequences

- A namespace override is no longer discarded when the namespace object baseline is empty, closing the
  principal silent-loss trap.
- Merge-mode environment-specific baselines are no longer dropped, closing the second silent-loss trap.
- No new hard failures are introduced, so no environment that generates today starts failing. Abnormal
  cases surface as warnings.
- Existing configurations keep loading because baseline stays optional in the schema.
- Making the parameter list optional creates a compatibility obligation: a consumer that still requires the
  list must treat an omitted list as an empty list.
- A corpus backward-compatibility scan found no divergences for the side gate, the within-side
  resolution, standalone overrides, and the empty-string normalization.
- Misconfigured overrides that target the wrong baseline are warned but not stopped. Generation
  continues, which means a misconfiguration can affect outputs without being caught automatically.
- The change spans the effective set calculator, the environment build step, the object schemas in
  both repositories, and the documentation.

See [the resource profile feature doc](/docs/features/resource-profile.md) for the resulting
user-facing behavior and the full resolution rules.
