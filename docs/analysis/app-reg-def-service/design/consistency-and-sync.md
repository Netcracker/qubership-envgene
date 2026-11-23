# Consistency and sync model

How the cache stays correct and fresh, and how writes stay safe. The flows these rules govern are in
[architecture.md](architecture.md), and the objects they move are in
[data-model-and-layout.md](data-model-and-layout.md).

The service is one deployable, not a set of networked services, so the in-process path is trivial. In the
lite profile one process holds the cache as a local map, the Indexer rebuilds it and the Resolver reads it,
and there is nothing to coordinate. The rules below bite where the design crosses a boundary and shares
state: the HA profile, with read replicas and a write and resync leader over a shared Redis cache, and the
multi-cluster case, with several instances over one git. Each section notes where it applies.

## The shared cache and its single writer

The Indexer is the only writer of the cache. The Resolver reads it, and the Writer writes git and never
touches it. In the lite profile that is one in-process map, so it is just the module layout. It earns its
name in the HA profile, where the write and resync leader is the only process that writes the shared Redis
cache and the read replicas only read, so the shared cache has no cross-process write race.

## Resync

A resync fetches the repo to HEAD and rebuilds the cache. It runs on two triggers:

- a push webhook, the prompt path. A push to the defs repo fires the webhook, which triggers a resync.
- a periodic resync, the safety net. A timer runs a resync regardless of webhooks, so a missed or
  undelivered webhook is caught within the interval.

Any change triggers a full repo resync, not an incremental diff. A resync is idempotent, it fetches and
re-parses to HEAD and rebuilds the cache from scratch, so duplicate or out-of-order webhook deliveries
converge on the same state. A malformed def is skipped per entry and logged, never an all-or-nothing
blackout, so one bad file cannot stall the rest.

The rebuild keeps a read correct across a resync by three properties:

- it is atomic. A read sees either the whole pre-resync snapshot or the whole post-resync one, never a
  mix. In lite that is a reference swap, in HA a swap in the shared store.
- it never moves the cache backward. Resyncs do not overlap, and across an HA leader handover a late
  rebuild from the old leader is kept only if its commit is newer, so it cannot regress to an older commit.
- it reflects exactly the defs at HEAD, so an add, a change, and a delete are all applied, a removed def
  dropped from the cache.

## Visibility

Reads are eventually consistent with writes. A write returns once its commit is pushed, and the cache
catches up through the resync the push triggers. A resolve immediately after a write may briefly see the
state before the write, for at most one resync.

If a consumer ever needs to see its own write immediately, the Writer can run a resync in process before
returning, which makes the write read-after-write consistent. That is deferred until a write-then-read
consumer appears.

## The commit race

Writes share one piece of state, the git remote. Three races, each settled by construction rather than by
a lock.

- Writer against writer. Writes go through one write and resync owner, the single process in the lite
  profile and the leader in the HA profile, so two writes never run at once within a cluster.
- Writer against resync. The Indexer resyncs on a read worktree and the Writer commits on a separate write
  worktree, so a resync and a write never contend on one checkout.
- Writer against an external or manual push. The Writer commits and pushes with a fetch-rebase retry on a
  non-fast-forward, so a concurrent push is absorbed by the rebase. A conflict surfaces only on a real
  overlap, two commits that change the same def.

## Multi-cluster consistency

Each cluster runs its own instance over the one shared git source of truth. Reads are local and eventually
consistent, every instance converges as it resyncs the same git. Writes go through git's own optimistic
concurrency, the fetch-rebase retry, so git is the cross-cluster write serializer with no distributed
lock. Each cluster holds one webhook, so a push notifies that cluster's resync owner, and the periodic
resync is the guarantee for a cluster that missed a delivery.

## Failure modes

- Git unreachable. The cache keeps serving its last state while the resync retries. Reads stay available
  and are stale until git returns.
- A missed webhook. The periodic resync catches the change within its interval.
- A malformed def. It is skipped per entry and logged, and the rest of the repo indexes normally.
- A restart. The instance re-clones and warms the cache from git before it becomes ready. In the HA
  profile the read replicas keep serving from the shared cache while a new leader warms.
