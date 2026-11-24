# Architecture

The service's components and its read, resync, and write flows. For the rest, see
[api-reference.md](api-reference.md) for the API contract,
[data-model-and-layout.md](../model.md) for the data model and repository layout,
[consistency-and-sync.md](consistency-and-sync.md) for the consistency rules, and
[deployment-and-operations.md](deployment-and-operations.md) for the operational detail.

## Scope

In scope now is the single-process service: resolve, the read and write interfaces, and the git sync, with
an in-process cache. High availability and horizontal scale-out, running several replicas behind a shared
cache and across clusters, are deferred, and so are authorization and multizone, with one zone today. The
design stays open to them: the cache can move to a shared store later. The rest of this page describes the
single-process service.

## System overview

The service is a runtime resolver and cache over a git source of truth, the dedicated defs repo. It
resolves an application to its `Application`, the AppDef attributes with its RegDef joined in as
`registry`.

It returns the RegDef with its `credId` references, not the secret values, and it never contacts a
registry. The consumer adds the version and the credentials to build the artifact and the provider and
download through the client and artifacts_finder.

```mermaid
flowchart LR
  consumers["Consumers"] -->|"resolve, read, write"| svc["appregdef service"]
  svc <-->|"fetch, push"| git[("git<br/>App Reg Def repo")]
  git -->|"webhook on push"| svc
```

## Components

One deployable with a small set of components. The calls between them are in-process.

```mermaid
flowchart TB
  authz["Authn and authz<br/>(deferred)"]
  subgraph svc["appregdef service"]
    api["Consumer API"]
    wh["Webhook receiver"]
    reader["Reader"]
    writer["Writer"]
    indexer["Indexer"]
    cache[("Cache")]
    gitad["Git client"]
  end
  authz -.-> api
  api -->|read| reader
  reader -->|lookup| cache
  api -->|write| writer
  wh -->|resync| indexer
  indexer -->|rebuild| cache
  indexer -->|fetch| gitad
  writer -->|commit, push| gitad
  classDef deferred stroke-dasharray:5 5,color:#777;
  class authz deferred;
```

| Component        | Responsibility                                                                              |
|------------------|---------------------------------------------------------------------------------------------|
| Consumer API     | exposes the API, validates requests, calls the Reader or the Writer                         |
| Webhook receiver | receives the git push notification and triggers a resync                                    |
| Reader           | returns a RegDef or AppDef by name, and for resolve joins them into the Application         |
| Cache            | holds the def objects by name, an in-process map now, swappable to a shared store later     |
| Indexer          | cache writer, resyncs the whole repo to HEAD on a webhook or a timer and rebuilds the cache |
| Writer           | create and update, validates then commits and pushes the def                                |
| Git client       | clone, fetch, commit, and push on the read and the write                                    |

## Data flows

### Read

```mermaid
sequenceDiagram
  actor C as Consumer
  participant API as Consumer API
  participant R as Reader
  participant Cache
  C->>API: resolve(app, zone?)
  API->>R: resolve
  R->>Cache: look up appdef and regdef by name
  Cache-->>R: the def objects
  R->>R: join the appdef and its regdef into the Application, as stored
  R-->>API: the Application, the appdef attributes with the resolved registry
  API-->>C: response
```

`getRegDef` and `getAppDef` are the same cache read without the join: the Reader returns the stored RegDef
or AppDef by name.

### Resync

```mermaid
sequenceDiagram
  participant GS as git server
  participant WR as Webhook receiver
  participant IX as Indexer
  participant GA as Git client
  participant Cache
  Note over GS,Cache: a resync runs on a push webhook or a periodic timer, the safety net for a missed webhook
  GS->>WR: webhook on push
  WR->>IX: resync
  IX->>GA: fetch to HEAD and read the whole repo
  GA-->>IX: all def files
  IX->>IX: parse, malformed entries skipped
  IX->>Cache: rebuild the cache to HEAD
```

### Write

```mermaid
sequenceDiagram
  actor C as Consumer
  participant API as Consumer API
  participant W as Writer
  participant GA as Git client
  C->>API: create or update a def
  API->>W: write request
  W->>W: validate the schema and the name
  W->>GA: commit and push on the write worktree, fetch-rebase retry on a non-fast-forward
  GA-->>W: pushed
  W-->>API: the written object
  API-->>C: object
```

A write returns once the commit is pushed. The cache catches up through the resync the push triggers, so
reads are eventually consistent with a write.
