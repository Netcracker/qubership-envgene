# Architecture

The service's components and its read, sync, and write flows. For the rest, see
[api-reference.md](api-reference.md) for the API contract,
[data-model-and-layout.md](data-model-and-layout.md) for the data model and repository layout,
[consistency-and-sync.md](consistency-and-sync.md) for the consistency rules, and
[deployment-and-operations.md](deployment-and-operations.md) for the operational detail.

## System overview

The service is a runtime resolver and cache over a git source of truth, the dedicated defs repo. It turns
`application:version` into the DD or SD download-info plus all registry sections and the appdef metadata,
auth-ready. It is blind on credentials: it returns the `authConfig` and the
credId references, and the consumer mints the secret with its own identity.

```mermaid
flowchart LR
  consumers["Consumers"] -->|"resolve, read, write"| svc["App Reg Def service"]
  svc <-->|"fetch, push"| git[("git<br/>App Reg Def repo")]
  git -->|"webhook on push"| svc
```

## Components

One deployable, laid out as ports and adapters, so the calls below are in-process rather than network
hops. Inbound adapters accept outside traffic, the core holds the logic, and outbound adapters sit behind
ports, as grouped in the diagram. The Git adapter works two separate worktrees, a read worktree the
Indexer syncs and a write worktree the Writer commits on, so the sync and write paths do not race on one
checkout. The Indexer is the single writer of the cache, the invariant that keeps reads correct
(see consistency-and-sync).

```mermaid
flowchart TB
  subgraph svc["App Reg Def service (one deployable)"]
    subgraph inb["inbound adapters"]
      api["Consumer API"]
      wh["Webhook ingest"]
    end
    subgraph cor["core"]
      resolver["Resolver"]
      indexer["Indexer<br/>sole cache writer"]
      writer["Writer"]
    end
    subgraph outb["outbound adapters, behind ports"]
      cache[("Cache<br/>in-proc or Redis")]
      gitad["Git adapter"]
    end
  end
  api -->|read| resolver
  resolver -->|lookup| cache
  api -->|write| writer
  wh -->|changed paths| indexer
  indexer -->|upsert| cache
  indexer --> gitad
  writer --> gitad
  writer -->|wait watermark| cache
  writer -. "notify SHA" .-> indexer
```

| Module         | Responsibility                                                                                        | Depends on                  |
|----------------|-------------------------------------------------------------------------------------------------------|-----------------------------|
| Consumer API   | exposes the REST surface, validates requests, authorizes, routes to the Resolver or the Writer        | Resolver, Writer            |
| Webhook ingest | validates the git HMAC and passes the changed paths to the Indexer                                    | Indexer                     |
| Resolver       | selects DD or SD from the appdef, assembles the resolve response, builds authReady (blind)            | Cache                       |
| Cache          | holds the def objects by name and exposes the watermark for read-after-write                          | -                           |
| Indexer        | sole cache writer, syncs git on a webhook or the backstop, incremental plus a periodic full reconcile | Git adapter, Cache          |
| Writer         | create and update, validates the schema and the name, commits and pushes, notifies the Indexer        | Git adapter, Indexer, Cache |
| Git adapter    | clone, fetch, commit, push, and the changed-path diff, on the read and the write worktrees            | -                           |

## Data flows

### Read

```mermaid
sequenceDiagram
  actor C as Consumer
  participant API as Consumer API
  participant R as Resolver
  participant Cache
  C->>API: resolve(app:version, zone?)
  API->>R: resolve
  R->>Cache: look up appdef and regdef by name
  Cache-->>R: the def objects
  R->>R: select DD or SD from the appdef, build authReady from authConfig and credId, no secret
  R-->>API: artifact (DD or SD) download-info, registry sections, authReady, appdef metadata
  API-->>C: response
```

### Sync

```mermaid
sequenceDiagram
  participant GS as git server
  participant WI as Webhook ingest
  participant IX as Indexer
  participant GA as Git adapter
  participant Cache
  Note over GS,Cache: sync is triggered by a push webhook or the periodic backstop
  GS->>WI: webhook with changed paths
  WI->>IX: trigger
  IX->>GA: fetch and diff (changed paths on a webhook, full tree on the backstop)
  GA-->>IX: changed def files
  IX->>IX: parse, malformed entries skipped
  IX->>Cache: upsert the entries, set the watermark to HEAD
```

### Write

```mermaid
sequenceDiagram
  actor C as Consumer
  participant API as Consumer API
  participant W as Writer
  participant GA as Git adapter
  participant IX as Indexer
  participant Cache
  C->>API: create or update a def
  API->>W: write request
  activate W
  W->>W: validate the schema and the name
  W->>GA: commit and push on the write worktree, fetch-rebase retry on a non-fast-forward
  GA-->>W: commit SHA
  W--)IX: notify the SHA
  IX->>GA: fetch on the read worktree
  IX->>Cache: upsert, set the watermark
  W->>Cache: block until the watermark covers the SHA
  Cache-->>W: the def object
  W-->>API: the written object
  deactivate W
  API-->>C: object
```

## Logical topology

The same modules run in two profiles. The split that matters at the logical level is the read plane
(Consumer API and Resolver over the Cache) versus the write and sync plane (Webhook ingest, Indexer,
Writer). In the lite profile both planes share one process. In the HA profile the read plane scales as
stateless replicas and the write and sync plane runs as one leader. The replica counts, the leader
election, the shared store, and the multi-cluster deployment are in
[deployment-and-operations.md](deployment-and-operations.md).

## Dependency direction

Dependencies point inward through ports, and the graph is acyclic: the Resolver reaches only the Cache,
and only the Indexer and the Writer reach git, each through the Git adapter. The Cache is warmed in full at
bootstrap and is authoritative, so a resolve miss is a not-found, never a git fallback on the read path.
This is what lets the cache move from in-process to Redis and the write and sync plane move to a separate
process without touching the read path.
