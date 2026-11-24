# App Reg Def - exploration brief

Working document for the app reg def service design. Living note: the Decision Log at the top is appended
to as decisions settle. The brief sections below fill in as the exploration converges, so incremental
fixing and the final brief are the same document.

Source diagram: drawio page "definitions" (`XoWvJGermGjVIPfKqKuA`). Status: discovery in progress, not a
committed change, no OpenSpec folder yet.

## Decision log

| #   | Decision                                                                     | Status    | Source            |
|-----|------------------------------------------------------------------------------|-----------|-------------------|
| D1  | Shape: git SOT plus service as a runtime access layer (both)                 | settled   | OQ1               |
| D2  | Credentials: blind (service returns authConfig, consumer mints)              | settled   | diagram           |
| D3  | DD and SBOM content processing is out of scope                               | settled   | -                 |
| D4  | Resolve returns artifact download-info plus all registry sections, v2        | settled   | research          |
| D5  | Def source: git only                                                         | settled   | extend            |
| D6  | Auth: v2 authConfig is the target source of truth                            | direction | challenge 7       |
| D7  | Resolve includes appdef metadata (release-name, argocd options)              | settled   | QA1               |
| D8  | getRegDef kept for version-independent registry access                       | settled   | QA2               |
| D9  | Write response returns the object, no separate verify GET                    | settled   | -                 |
| D10 | Create and update are separate operations, not one upsert                    | settled   | -                 |
| D11 | Consumer builds sub-artifact URLs, no sub-resolve API                        | settled   | QA4               |
| D12 | Auth within a zone: registry-side form plus ambient identity                 | settled   | O1                |
| D13 | One default zone now, multizonality deferred (optional zone param)           | settled   | zones             |
| D14 | Dedicated defs repo (def store), separate from instance repos                | settled   | G1.1              |
| D15 | Flat layout, zone folders deferred                                           | settled   | G1.2              |
| D16 | Single branch is the SOT, optional manual MR workflow (open)                 | settled   | G1.3              |
| D17 | Zero secrets in the repo, credId refs only, no encryption                    | settled   | G1.4              |
| D18 | Casing by role: kind PascalCase, path identifiers kebab, fields camelCase    | settled   | industry          |
| D19 | Folders: application-definitions/ and registry-definitions/                  | settled   | G1.2              |
| D20 | Resync triggered by a push webhook plus a periodic timer, not poll-only      | settled   | G2.1              |
| D21 | Any change triggers a full repo resync, incremental resync deferred          | settled   | G2.3              |
| D22 | Single-layer cache of def objects, resolve on the fly, memo deferred         | settled   | G3.1              |
| D23 | Cache store in-process per replica, Redis-ready for shared HA                | settled   | G3.2              |
| D24 | Indexer is the sole cache writer, the Writer commits and pushes only         | settled   | C1 critic         |
| D25 | Separate git working copies for resync-read and write, settles G8            | settled   | C1 critic         |
| D26 | Webhook receiver is a separate component from the consumer API               | settled   | C1 critic         |
| D27 | Deployment schemas: lite (in-proc) and HA (Redis) from one codebase          | settled   | C2                |
| D28 | Multi-cluster: one instance per cluster over the shared git SOT              | settled   | C2                |
| D29 | Webhook: one per cluster to the resync owner, no pub/sub, periodic timer     | settled   | C2                |
| D30 | Write returns on commit, cache is eventually consistent via resync           | settled   | C2                |
| D31 | Malformed def is skipped per entry, not an all-or-nothing blackout           | settled   | C2                |
| D32 | Runtime version-agnostic, store v2, v1-to-v2 a one-time migration CLI        | settled   | challenge         |
| D33 | Service targets the extended RegDef v2, schema brought up to it              | settled   | challenge         |
| D34 | Resolve returns the Application model (AppDef with embedded RegDef v1 or v2) | settled   | artifact-searcher |
| D35 | credId to credential processing stays in the client, feeds the provider      | settled   | challenge         |

## Change class

Architectural. A new capability with an interface that EnvGene, DPG, and other consumers depend on.

## Design constraints

- Multizone-extensibility: multizonality is deferred (P2) and the design proceeds without it. Validate
  each decision against adding it later without a breaking change. The `resolve` API reserves an optional
  zone selector as the hook, and there is one default zone today.

## Backlog

Open work, grouped. The Decision Log above holds settled decisions. Migration is a separate one-time CLI
(DL5). Current focus: the deliverables (OpenAPI and algorithms) now that components and topology are settled.

Open questions (API shaping):

- O2 - is a standalone `getAppDef(name)` (by name, no version) needed, or does the appdef content fold
  into `resolve`, the write response, and `list`? Lean drop.
- O3 - are `listRegDefs` / `listAppDefs` needed, and with what filter? No hard consumer seen. Lean drop.
- O4 - is the delivery case served by distinct named defs or by the zone mechanism?

Git and write policy:

- G6 - are manual or external commits to the repo allowed? The mechanism is handled (an external commit
  takes the Indexer path, D30), the policy and the optional MR-branch workflow (D16) are still open.

Cross-cutting:

- X1 - observability: refine the metrics and the SLO (sketched in Topology and deployment).
- X2 - security and authz: refine the authn model for the consumer API (sketched in Topology).
- X4 - rollout: replace the two resolvers (artifact-searcher, DPG) with coexistence or a shadow mode.
- X6 - failure modes: refine beyond the Topology sketch if needed.
- X7 - a resolve-response version signal (did the answer change?), a change signal for consumers.
- X8 - put the defs JSON schema in the defs repo, so the service and the library validate against a
  versioned schema committed there, selected by the def version, additive-only within a major with the JSON
  Schema draft pinned. Decouples validation from a code release, not behaviour, the provider and auth
  mapping stays code. Open: whether to adopt and the compatibility policy. Analogue: k8s CRD, schema registry.

Deliverables (end of design):

- DL1 - OpenAPI specs for the resolve, read, and write interfaces.
- DL2 - algorithm descriptions with sequence diagrams: resolve, auth-ready assembly, DD vs SD
  discrimination, write and commit.
- DL3 - the components and deploy scheme, detailed enough to implement. Largely in Topology and deployment.
- DL4 - DTO and response schemas plus the error model.
- DL5 - the v1-to-v2 migration CLI and its spec, a one-time tool separate from the runtime service. Its
  scope includes normalizing legacy def names to the kebab DNS-safe convention (no spaces) with
  coordinated `registryName` updates (was P3).

Parked:

- P1 - the write API (create and update). The shape is settled, the git-write design is in Topology and
  deployment. On create, the def name is validated or normalized to the kebab DNS-safe convention (validate
  vs auto-transform is a sub-choice).
- P2 - multizonality. The design stays extensible to it (D13).
- P4 - incremental resync by changed paths. Deferred. The webhook and the periodic timer both do a full repo
  resync for now, to be revisited if the resync cost matters.

Todo:

- T1 - how RegDef v2 affects EnvGene and DPG.
- T2 - bring `regdef-v2.schema.json` up to the extended v2 (registries list by artifactType,
  accessRoles, credId, url plus repoName) and add a `kind` to the RegDef and `appdef.schema.json`.
- T3 - revisit `solutionDescriptor` (a boolean on the AppDef) when the interfaces are discussed: how
  it maps to the resolve artifact kind DD or SD.

## Problem / why

`application:version` -> artifact resolution, together with registry and credential resolution, is
duplicated across at least two resolvers with their own models:

- `artifact-searcher` (`Registry` / `RegistryV2`) for the git / EnvGene flow.
- DPG (`UnifiedRegDef` / `RegistryInfo`) for deploy-plan building.
- The internal extend adds a third, CMDB-backed `appver_resolver`, which is out of scope here.

The duplication carries fragile seams: the purl (package URL) `repository_id` pointer-name contract, the
registry-name key reconciliation (`quote` on write vs `%20` un-escape on read), and a v1->v2 projection
that runs only
for aws and gcp. The DD is even resolved and downloaded twice, by EnvGene and DPG independently, over a
shared on-disk cache.

A single service over the git source-of-truth unifies resolution, gives cheap API plus cache access
instead of a git clone, and standardizes on RegDef v2.

## Current behavior

Grounded in code research, provenance kept inline.

- Two resolvers resolve and download the DD: EnvGene `scripts/effective_set/dd_downloading.py:115` and
  DPG `modules/dpg/.../artifact_descriptor/finder.py:90`, each with its own cache.
- Helm app chart: resolved, downloaded, and unpacked by EnvGene only, to feed SBOM
  (`dd_downloading.py:125-126`). DPG does not download the chart.
- Docker image: resolved to coordinates only (`IMAGE_REPOSITORY`, `docker_registry`, `full_image_name`),
  never pulled by EnvGene or DPG, the deployer pulls it (`BomReaderUtilsImplV2.java:226-320`,
  `BomCommonUtils.java:146`).
- go / npm / raw: never resolved or downloaded via app:version (`FileExtension` is only ZIP / JSON,
  `models.py:294-296`).
- Auth is param-driven today: cloud auth (assume_role, federation, oauth2) is assembled from
  `pubreg_params.yaml` pipeline params, not from the def's `authConfig`. The v2 `authConfig` schema
  exists but has no runtime reader. In OSS `artifact-searcher`, assume_role / federation / oauth2 are
  `NotImplementedError`.
- Write path: defs are rendered from templates (`AppregdefRenderStep`), written to `regdefs/` and
  `appdefs/` (root and dual placement), user-overridden file-level, then committed.

## Intended behavior / cases

Resolve surface and response-format orientation:

```yaml
resolve( app:version | [app:version, ...], zone? ):
  # per app:
  artifact:            # the DD or the SD at these coordinates, not named DD-only
    kind: DD | SD
    gav: ...
    downloadUrl: ...
  authReady: ...       # provider/method + non-secret params + cred ref (blind), registry-level
  registry:            # all registry sections present in the def
    maven: ...
    docker: ...
    helm: ...
    helmApp: ...
    go: ...
    npm: ...
    raw: ...
```

The consumer downloads the DD or SD and the chart over API or HTTP. The service does not download or
parse them. The docker image is pulled by the deployer.

## API surface

Derived from the responsibilities above. This is the list, not the detailed contracts.

Read and resolve:

- `resolve(app:version, zone?)` - artifact (DD or SD) download-info, all registry sections, and appdef
  metadata, auth-ready (blind). `zone` is optional with one default zone today. Core.
- `resolveBatch([app:version])` - the `resolve` result per entry. Core.
- `getRegDef(name)` - the v2 reg def object, for version-independent access (publish and
  promote). Core.
- `getAppDef(name)` - the app def object. Open (O2).
- `listRegDefs(filter)` / `listAppDefs(filter)` - a list of defs. Open (O3), filter included.

Write (parked, P1). Create and update are separate operations, and each returns the written object:

- `createRegDef` / `createAppDef` - create a new def, fail if it exists.
- `updateRegDef` / `updateAppDef` - update an existing def, fail if it is absent.

Deliberately absent: a raw def file (git serves that), artifact download (the consumer downloads over
API or HTTP), credential minting (blind, D2), a resolve-by-SD entry (the caller expands the SD into a
list of `app:version`), a sub-artifact resolve (the consumer builds docker and chart URLs from the
registry sections, D11), and CMDB access (D5).

## Decision and rejected alternatives

- Shape (D1): both. Rejected: service-only (nowhere to store defs), git-only (a clone per access, no
  single cheap API).
- Credentials (D2): blind. Rejected: a broker that mints and hands out secrets, which puts identity in
  the service.
- Scope (D3): resolve, do not process content. Rejected: a content engine that parses DD and builds SBOM.
- Source (D5): git only. Rejected: fronting CMDB as well, the internal extend's model.
- Auth (D6): v2 `authConfig` as the single source of truth. Rejected: keep the param-driven
  `pubreg_params` model. Accepted cost: net-new auth readers in OSS, and a v1/v2 coexistence window
  during migration.

## Entities / contracts

- AppDef (`schemas/appdef.schema.json`): thin pointer - `name`, `registryName`, `groupId`, `artifactId`,
  `solutionDescriptor`, `deployParameters`, `technicalConfigurationParameters`, `metadata`.
- RegDef v1 (`schemas/regdef.schema.json`) / v2 (`schemas/regdef-v2.schema.json`): registry coordinates
  plus auth. v1 has a single `credentialsId`, v2 has an `authConfig` map.
- DD: the maven artifact the AppDef points to - services, configurations, smartplug, charts. Not served
  by the service.
- The resolve response shape above is the contract this service exposes.

## Topology and deployment

Two deployment schemas from one codebase, selected by config (the cache is a port, D23): lite and HA. A
malformed def is skipped and logged, never an all-or-nothing blackout (D31). A resync is idempotent (fetch
and re-parse to HEAD), so duplicate or out-of-order webhook deliveries converge.

Lite deployment schema (form 1, ship first):

- One `Deployment`, `replicas: 1`, `Recreate` strategy, so a rollout never runs two pods writing git.
- All components in one process, in-process cache, `emptyDir` for the git working copies, no PVC, rebuilt
  from git on start.
- Bootstrap: clone the branch (D16), parse every def into the cache, become ready.

HA deployment schema (form 2, additive):

- Read-service: a `Deployment` of N stateless replicas (API plus Resolver) that read the shared Redis
  cache and hold no git.
- Write/resync singleton: one active instance (leader-elected via a k8s Lease) that owns the git working
  copies, the Indexer, the Writer, and the webhook receiver, and writes the shared Redis cache.
- Redis holds the cache (`defs:appdef:<name>`, `defs:regdef:<name>`) and needs its own HA.
- Routing: read verbs go to the read-service, write verbs and the webhook go to the singleton.

Git working copies (both deployment schemas):

- Read worktree (Indexer): one shallow, blob-filtered, sparse checkout of application-definitions/ and
  registry-definitions/ (D19). A resync is a `git fetch` to HEAD plus a full re-read of the checkout (D21).
- Write worktree (Writer): an ephemeral worktree per write, committed, pushed, then discarded (D25).

Write and visibility (D30): a write validates, commits, and pushes with a fetch-rebase retry on a
non-fast-forward, then returns the written object (D9). The push fires the webhook, so the write takes the
same resync path as an external or manual commit (G6), and the cache is eventually consistent. If a consumer
ever needs to see its own write immediately, the Writer can run an in-process resync before returning.

Multi-cluster (D28): one independent instance per cluster over the one shared git SOT. Reads are local and
eventually consistent as each instance resyncs the same git. Writes go through git's own optimistic
concurrency (the fetch-rebase retry), so git is the cross-cluster write serializer with no distributed
lock. Each cluster picks its own deployment schema.

Webhook delivery (D29): the repo holds one webhook per cluster, so the cross-cluster fan-out is at cluster
granularity, which is viable because clusters are few and stable. Inside a cluster the webhook reaches the
single resync owner (the one pod in lite, the singleton leader in HA) and Redis fans out to the read pods.
There is no pub/sub. The periodic resync is the guarantee for any missed delivery.

Ports and network: :8080 consumer API, :8081 webhook receiver (HMAC), :8082 health, :9090 metrics, each
behind its own NetworkPolicy. Consumers reach a Service, the git server reaches a webhook Ingress.

Security (X2): webhook HMAC, consumer authn and authz, git credentials as a least-privilege Secret, and the
blind boundary (the service reads credId references only and never holds a registry secret, D2 and D17).

Observability (X1): resolve latency, cache entry counts, resync lag (time since the last resync),
webhook deliveries and failures, write latency, and the conflict rate.

Failure modes (X6): git unreachable serves the stale cache while the periodic resync retries, a missed webhook is
caught by the periodic resync, a malformed def is skipped per entry (D31), and a restart re-clones and warms (in
HA the read pods keep serving from Redis).

Provenance note: current-behavior claims are grounded in code research over qubership-envgene and the
internal extend repo (env-generator-2). The load-bearing file:line citations are inlined above.
