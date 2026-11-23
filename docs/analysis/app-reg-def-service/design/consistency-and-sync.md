# Consistency and sync model

> _Placeholder. The hard part in one place: how the cache stays correct and fresh, how read-after-write is
> guaranteed, and how writes race safely. The analogue of Colly's versioning doc._

## Cache and the single-writer invariant

> _Placeholder. The Indexer is the sole writer of the cache. The Writer never mutates the cache, it commits
> and notifies. Why this removes the two-writer race._

## Sync

> _Placeholder. Webhook-primary plus a periodic backstop, incremental by changed paths, and idempotent
> (fetch and re-parse to HEAD) so duplicate or out-of-order deliveries converge._

## Watermark and read-after-write

> _Placeholder. The cache carries the last indexed commit SHA. A write waits until the watermark covers its
> commit before returning the object. An external or manual commit takes the same Indexer path._

## The commit race

> _Placeholder. Writer vs writer, writer vs sync (separate working copies), and writer vs external push
> (fetch-rebase retry, a conflict on a real overlap)._

## Multi-cluster consistency

> _Placeholder. One instance per cluster over the shared git. Reads are eventually consistent. Git is the
> cross-cluster write serializer through its own optimistic concurrency._

## Failure modes

> _Placeholder. Git unreachable serves stale, a missed webhook is caught by the backstop, a malformed def
> is skipped per entry._
