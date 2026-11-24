# Consistency and sync model

How the cache stays correct and fresh, and how writes stay safe. The flows these rules govern are in
[architecture.md](architecture.md), and the objects they move are in
[data-model-and-layout.md](../model.md).

The service runs as one process. One process holds the cache as a local map, the Indexer rebuilds it and
the Reader reads it, and there is nothing to coordinate. The rules below keep that cache correct and
writes safe. High availability and multi-cluster are deferred, see the Scope in
[architecture.md](architecture.md).

## The cache and its single writer

The Indexer is the only writer of the cache. The Reader reads it, and the Writer writes git and never
touches it. That is one in-process map, so the single-writer rule is just the module layout. It is what
keeps a read correct while a resync rebuilds the cache.

## Resync

A resync fetches the repo to HEAD and rebuilds the cache. It runs on two triggers:

- a push webhook, the prompt path. A push to the defs repo fires the webhook, which triggers a resync.
- a periodic resync, the safety net. A timer runs a resync regardless of webhooks, so a missed or
  undelivered webhook is caught within the interval.

Any change triggers a full repo resync, not an incremental diff. A resync is idempotent. It fetches and
re-parses to HEAD and rebuilds the cache from scratch, so duplicate or out-of-order webhook deliveries
converge on the same state.

A malformed def is skipped per entry and logged, never an all-or-nothing blackout, so one bad file
cannot stall the rest.

## Visibility

Reads are eventually consistent with writes, since the write and the resync that catches the cache up are
separate steps. A write returns once its commit is pushed, and the cache catches up through the resync
the push triggers. A resolve immediately after a write may briefly see the state before the write, for
at most one resync.

If a consumer ever needs to see its own write immediately, the Writer can run a resync in process before
returning, which makes the write read-after-write consistent. That is deferred until a write-then-read
consumer appears.

## The commit race

Writes share one piece of state, the git remote. Three races, each settled by construction rather than by
a lock.

- Writer against writer. All writes go through the one process, so two writes never run at once.
- Writer against resync. The Indexer resyncs on a read worktree and the Writer commits on a separate write
  worktree, so a resync and a write never contend on one checkout.
- Writer against an external or manual push. The Writer commits and pushes with a fetch-rebase retry on a
  non-fast-forward, so a concurrent push is absorbed by the rebase. A conflict surfaces only on a real
  overlap, two commits that change the same def.

## Failure modes

- Git unreachable. The cache keeps serving its last state while the resync retries. Reads stay available
  and are stale until git returns.
- A missed webhook. The periodic resync catches the change within its interval.
- A malformed def. It is skipped per entry and logged, and the rest of the repo indexes normally.
- A restart. The instance re-clones and warms the cache from git before it becomes ready.
