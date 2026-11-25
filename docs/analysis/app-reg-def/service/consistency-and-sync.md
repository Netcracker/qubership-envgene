# Consistency and sync model

How the cache stays correct and fresh, and how writes stay safe. The flows these rules govern are in
[architecture.md](architecture.md), and the objects they move are in
[data-model-and-layout.md](../model.md).

The service runs as stateless replicas in more than one cluster, each with its own in-memory cache. Within a replica
the Indexer rebuilds the cache and the Reader reads it. Across replicas, and across clusters, there is
nothing to coordinate: each replica syncs the one git on its own and they converge. The rules below keep
each cache correct, writes safe, and the replicas convergent.

## The cache and its single writer

Within each replica the Indexer is the only writer of its cache. The Reader reads it, and the Writer
writes git and never touches the cache. The cache is a per-replica in-memory map, so the single-writer
rule is just the module layout. It keeps a read correct while a resync rebuilds the cache, and since
replicas share no cache there is no cross-replica write race on it.

## Resync

A resync fetches the repo to HEAD and rebuilds the cache. Each replica resyncs on its own, two triggers:

- a periodic poll, the backbone. Every replica polls git on an interval, with jitter so the replicas do
  not all fetch at once, the pull model of CoreDNS, Flux, and Argo CD.
- a push webhook, a best-effort speed-up. A push fires the webhook, but it reaches one replica through the
  cluster load balancer and freshens only that one. There is no cross-replica fan-out, so the poll brings
  every other replica up to date.

Any change triggers a full repo resync, not an incremental diff. A resync is idempotent. It fetches and
re-parses to HEAD and rebuilds the cache from scratch, so duplicate or out-of-order webhook deliveries
converge on the same state.

A malformed def is skipped per entry and logged, never an all-or-nothing blackout, so one bad file
cannot stall the rest.

## Write visibility

A write is visible to a replica only after that replica's next resync, not when the write returns: the
write returns once its commit is pushed, and each replica catches up on its own poll, or on the best-effort
webhook if it lands there. A read may see the pre-write state for at most one poll interval, and two
replicas may briefly differ by one commit. Synchronous read-after-write, where the writing replica resyncs
in process before returning, is deferred until a write-then-read consumer needs it.

## The commit race

Writes share one piece of state, the git remote. The races are settled by git and by the worktree split,
not by a lock.

- Concurrent writers, two replicas or a replica against an external or manual push. Any replica can write.
  Each commits and pushes with a fetch-rebase retry on a non-fast-forward, so a concurrent push is absorbed
  by the rebase. A conflict surfaces only on a real overlap, two commits that change the same def.
- Writer against resync. Within a replica the Indexer resyncs on a read worktree and the Writer commits on
  a separate write worktree, so a resync and a write never contend on one checkout.

## Failure modes

- Git unreachable. The cache keeps serving its last state while the resync retries. Reads stay available
  and are stale until git returns.
- A missed webhook. The periodic resync catches the change within its interval.
- A malformed def. It is skipped per entry and logged, and the rest of the repo indexes normally.
- A replica loss. The other replicas keep serving, each from its own cache, so the cluster stays available.
- A restart. The replica re-clones and warms its cache from git before it becomes ready.
- A write conflict. When two commits change the same def at once, the fetch-rebase retry cannot absorb the
  push and the write returns a conflict for the caller to retry.
