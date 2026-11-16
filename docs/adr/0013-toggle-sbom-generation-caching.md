# ADR-0013: Toggle SBOM generation caching per repository

Status: Proposed

## Context and problem statement

A generated SBOM carries the container-image registry addresses of its components, and those addresses
differ from zone to zone. SBOM generation caches its output in the shared `/sboms/` directory of the
Instance Repository, keyed by application name, and regenerates an SBOM only when its cached file is
absent. When one Instance Repository serves environments in several zones, the first environment commits
an SBOM carrying its own zone's addresses, and an environment in another zone finds the file present,
skips regeneration, and silently deploys against the wrong registry. The operator of such a repository has
no way to opt out of the cache.

## Decision drivers

- An environment must never inherit another zone's registry addresses.
- The Instance Repository should not grow without bound to hold per-zone SBOMs.
- The cache must keep its value for the common single-zone repository, which is the default.

## Considered options

- Option A: an instance-global toggle that turns SBOM caching off for the whole repository.
- Option B: store SBOMs per environment instead of in a shared directory.
- Option C: make the regeneration criterion registry-aware, so a zone mismatch forces regeneration.
- Option D: always reconstruct coordinates from the registry definition during generation.

## Decision outcome

Chosen: Option A, because it removes the wrong-zone reuse at its root for the narrow set of repositories
that span zones, while leaving every single-zone repository on the cache it benefits from.

SBOM caching stays on by default, so the common repository is unaffected. An operator turns it off for a
whole repository, and from then on SBOM generation regenerates every application on every run, uses the
fresh SBOMs for that run, and removes the committed SBOM cache in full rather than leaving any of it
behind, so each zone's environment resolves its own registry addresses. The toggle is a per-repository stance rather than a per-environment one, because the shared
cache cannot be half-kept: an environment that removes it would strip the cache every other environment
relies on.

## Pros and cons of the options

### Option A: instance-global caching toggle (chosen)

- Good, because an environment in any zone regenerates its own SBOM and never reads another zone's
  addresses.
- Good, because the default leaves the single-zone repository and its cache untouched.
- Neutral, because the repository that turns caching off keeps no SBOM history, which it does not want
  anyway.
- Bad, because caching off means regeneration on every run, a performance cost and a hard dependency on
  the registry being reachable each run, and the operator must set the toggle by hand.

### Option B: per-environment SBOM storage

- Good, because each environment would hold its own correct SBOM.
- Bad, because a separate SBOM per environment grows git history and repository size for every
  repository, not only the ones that span zones.

### Option C: registry-aware regeneration criterion

- Good, because it would keep a cache while detecting a zone mismatch.
- Bad, because the criterion would differ per environment and force regeneration on nearly every run,
  erasing the benefit the cache exists to provide.

### Option D: always reconstruct coordinates from the registry definition

- Good, because reconstruction would yield the correct per-zone address when generation runs.
- Bad, because generation does not run at all when the cached file is present, so the second zone still
  reads the first zone's committed SBOM and reconstruction never fires.

## Consequences

- Positive: a repository spanning zones can guarantee each environment resolves its own registry
  addresses, and it no longer carries an SBOM cache that bloats it.
- Positive: SBOM retention has nothing to do in such a repository, because nothing is persisted.
- Negative: a repository with caching off regenerates SBOMs on every run, which costs time and requires
  the registry to be reachable on each run, and the operator must opt in to this per repository.

## More information

- Specs: [sbom-generation-caching](../../openspec/changes/sbom-cache-toggle/specs/sbom-generation-caching/spec.md)
- Proposal: [sbom-cache-toggle](../../openspec/changes/sbom-cache-toggle/proposal.md)
