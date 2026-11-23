# Architecture decision records

> _Placeholder. One ADR per load-bearing decision, rendered from the brief Decision Log. Each ADR is a
> short MADR record: context, options, decision, consequences._

Planned records:

- 0001 - Shape: git source of truth plus a runtime service (both).
- 0002 - Blind credentials: the service returns authConfig, the consumer mints the secret.
- 0003 - Resolve surface, not a content engine (no DD or SBOM processing).
- 0004 - Def source is git only (CMDB not fronted).
- 0005 - v2 authConfig as the target source of truth for registry auth.
- 0006 - Single cache writer (Indexer) and separate git working copies for sync and write.
- 0007 - Two deployment schemas (lite and HA) and the multi-cluster model.
