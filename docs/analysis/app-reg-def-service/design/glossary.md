# Glossary

Terms used across the App Reg Def service design docs, one line each. Filled as the design settles, so
a term lands here once it is used in a sibling doc.

- **App Reg Def service** - the runtime resolver and cache over the git defs repo that turns
  `application:version` into artifact download-info, registry sections, and appdef metadata, blind on
  credentials.
- **AppDef** - the application definition, a thin pointer with `name`, `registryName`, `groupId`,
  `artifactId`, `solutionDescriptor`, and metadata.
- **authConfig** - the v2 RegDef auth block, the provider and method plus non-secret parameters and a
  credId reference, never a secret value.
- **authReady** - the resolve response's assembled auth, the authConfig plus the credId reference, ready
  for the consumer to mint a secret with its own identity.
- **backstop** - retired term, see periodic resync.
- **blind** - the service returns the authConfig and the credId references and never reads or holds a
  registry secret, the consumer mints it.
- **Cache** - the driven adapter that holds the def objects by name and the watermark, in-process or Redis.
- **Consumer API** - the inbound REST adapter that validates and authorizes requests and routes them to the
  Resolver or the Writer.
- **core** - the application-logic modules, the Resolver, the Indexer, and the Writer.
- **credId** - a reference to a credential in an external store, carried in the authConfig, never the secret
  itself.
- **DD** - the Deployment Descriptor, the maven artifact an AppDef points to, with services,
  configurations, and charts. Not served by the service.
- **def** - a definition in the repo, an AppDef or a RegDef, one file per def.
- **defs repo** - the dedicated git repository that is the source of truth for all defs, separate from the
  instance repos. Also def store.
- **Git adapter** - the driven adapter for git, clone, fetch, commit, and push on the read and write
  worktrees.
- **HA profile** - the deployment profile with N stateless read replicas and one leader-elected write and
  resync singleton over a shared Redis cache.
- **Indexer** - the core module that is the sole cache writer, resyncs the repo to HEAD, and rebuilds the
  cache.
- **lite profile** - the single-process deployment profile with an in-process cache, shipped first.
- **periodic resync** - a resync run on a timer as the safety net for a missed webhook. Replaces the term
  backstop.
- **read worktree** - the git checkout the Indexer resyncs, separate from the write worktree so resync and
  write do not race.
- **read-after-write** - the guarantee that a write returns only after the watermark covers its commit, so
  the written object is readable.
- **RegDef** - the registry definition, registry coordinates plus auth. v1 has a single `credentialsId`, v2
  has an `authConfig` map.
- **registry sections** - the per-type registry blocks in a def, maven, docker, helm, helmApp, go, npm, and
  raw.
- **resolve** - the core operation, turn `application:version` into artifact download-info, registry
  sections, authReady, and appdef metadata.
- **resolveBatch** - resolve for a list of `application:version` entries.
- **Resolver** - the core module that assembles the resolve response from cached objects and builds
  authReady.
- **resync** - the Indexer operation, fetch the repo to HEAD and rebuild the cache. Runs on a push webhook
  or a periodic resync.
- **SD** - the Solution Descriptor, a list of `application:version` entries. The caller expands it into
  resolve calls.
- **watermark** - the last indexed commit SHA the Cache carries, used for read-after-write.
- **Webhook receiver** - the inbound adapter that validates the git HMAC and triggers a resync.
- **write worktree** - the ephemeral git checkout the Writer commits and pushes on, discarded after each
  write.
- **zone** - a selector for a registry set, for example onsite or offsite. One default zone today,
  multizone deferred.
