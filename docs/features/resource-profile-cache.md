# Resource profile cache

- [Overview](#overview)
- [How the cache works](#how-the-cache-works)
- [Configuration](#configuration)
  - [Enable the cache](#enable-the-cache)
  - [Disable the cache](#disable-the-cache)
- [Behavior](#behavior)
- [Related documentation](#related-documentation)

## Overview

Large [Resource Profile](/docs/features/resource-profile.md) files take noticeable time to parse during
Environment generation. The resource profile cache keeps each parsed profile on disk, so the next run that reads
the same file content loads the parsed result instead of parsing the YAML again.

The cache lives in `/.shared/profile-cache/` in the Instance repository working directory. It is useful only when
the GitLab CI cache carries `/.shared/` between instance pipeline runs. Without the GitLab CI cache, every run
starts with an empty cache directory.

## How the cache works

The cache covers two kinds of files read during Environment generation:

- Template Resource Profile Overrides
- Environment-specific Resource Profile Overrides

Each cache entry is keyed by the SHA-256 hash of the profile file content. A changed file gets a new key, so a stale
entry is never used. EnvGene does not delete old entries. The GitLab CI cache settings control how long the cache
lives.

The `/.shared/` directory is excluded from Git in the instance pipeline checkout. The cache survives the checkout
cleanup and is never staged for commit by EnvGene.

## Configuration

The cache is controlled by `cache.enabled` in [`config.yml`](/docs/envgene-configs.md#configyml). The default value
is `true`.

### Enable the cache

Keep the default and add `.shared/` to the `cache:` paths of the instance pipeline job:

```yaml
cache:
  key: envgene-shared
  paths:
    - .shared/
```

### Disable the cache

Set `cache.enabled` to `false` when the instance pipeline has no GitLab CI cache for `/.shared/`:

```yaml
cache:
  enabled: false
```

> [!WARNING]
> With the cache enabled and no GitLab CI cache for `/.shared/`, every run writes cache files that no later run
> reads. The files stay in the Instance repository working directory.

## Behavior

| Condition                                  | Result                                          |
|--------------------------------------------|-------------------------------------------------|
| `cache.enabled: false`                     | Profiles are parsed, nothing is written to disk |
| `CI_PROJECT_DIR` is not set                | Profiles are parsed, nothing is written to disk |
| No entry for the file content              | Profile is parsed and the entry is written      |
| Entry exists for the file content          | Profile is loaded from the entry                |
| Entry is unreadable                        | Warning is logged, profile is parsed            |
| Cache directory is not writable            | Warning is logged, generation continues         |

The cache never fails Environment generation. On any cache error, EnvGene falls back to parsing the profile file.

## Related documentation

- [Resource profiles](/docs/features/resource-profile.md)
- [`config.yml`](/docs/envgene-configs.md#configyml)
- [Environment Instance Generation](/docs/features/environment-instance-generation.md)
