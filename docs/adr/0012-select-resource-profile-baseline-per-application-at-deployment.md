# ADR-0012: Select the resource profile baseline per application at deployment

Status: Proposed

## Context

Applications of one namespace must be deployable with different baselines. Today the baseline is set for the whole
namespace, so teams change it before every deployment or keep a second logical environment.

## Decision

- An override can set a baseline per application. It takes precedence over every other baseline for that
  application, because the override already lists applications by name.
- A deployment takes an optional profile name, one string for every application of the run, as the legacy deployer
  did. The name is one of the standard baselines `dev`, `prod`, `dev-ha`, `prod-nonha`, or `reset`, so a wrong
  value fails before anything is written.
- EnvGene saves the selection in Git, so later deployments keep it without repeating it. Value `reset` removes
  the selection.

Rejected:

- A map of applications to baselines, because no case needs different baselines in one deployment.
- The inventory content input, because it replaces whole files and exposes the repository layout to the caller.
- A profile for one run only, because the setting must persist.

## Consequences

- A second logical environment is no longer needed.
- A deployment now changes configuration, and the selection applies to later deployments by other people.
- Baseline precedence gains a level.
- When the cloud has a profile and the namespace has none, the first deployment with a profile name makes the
  namespace use its own profile, and the cloud profile stops applying to it.
- An override with a per-application baseline cannot be imported into CMDB.

See [ADR-0006](/docs/adr/0006-resource-profile-baseline-override-resolution.md) and
[the resource profile feature doc](/docs/features/resource-profile.md).
