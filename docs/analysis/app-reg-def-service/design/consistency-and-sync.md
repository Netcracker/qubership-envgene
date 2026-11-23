# Consistency and sync model

How the cache stays correct and fresh, and how writes stay safe. The flows these rules govern are in
[architecture.md](architecture.md), and the objects they move are in
[data-model-and-layout.md](data-model-and-layout.md).

## Cache and the single-writer invariant

The Indexer is the sole writer of the cache. The Resolver only reads it, and the Writer only commits and
pushes to git, it never touches the cache. Every cache mutation goes through one component.

This removes the two-writer race. If both the Writer and the resync could write the cache, they would race
on the same entries, and a late write could overwrite a fresher resync. With one writer, all mutations are
serialized and the cache is always a coherent snapshot of a single git commit.

## Resync

A resync fetches the repo to HEAD and rebuilds the cache. It runs on two triggers:

- a push webhook, the prompt path. A push to the defs repo fires the webhook, which triggers a resync.
- a periodic resync, the safety net. A timer runs a resync regardless of webhooks, so a missed or
  undelivered webhook is caught within the interval.

Any change triggers a full repo resync, not an incremental diff. A resync is idempotent, it fetches and
re-parses to HEAD and rebuilds the cache from scratch, so duplicate or out-of-order webhook deliveries
converge on the same state. A malformed def is skipped per entry and logged, never an all-or-nothing
blackout, so one bad file cannot stall the rest.

## Visibility

Reads are eventually consistent with writes. A write returns once its commit is pushed, and the cache
catches up through the resync the push triggers. A resolve immediately after a write may briefly see the
state before the write, for at most one resync.

If a consumer ever needs to see its own write immediately, the Writer can run a resync in process before
returning, which makes the write read-after-write consistent. That is deferred until a write-then-read
consumer appears.

## The commit race

Three races, each settled by construction rather than by a lock.

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
