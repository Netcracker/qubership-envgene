# ADR-0008: Clean the reused node working tree at checkout start

Status: Proposed

## Context

To shorten checkout, a run fetches and sparsely checks out on a reused runner node instead of cloning fresh. A fresh
clone gave every run a pristine tree, but fetch with sparse checkout does not, so untracked artifacts of previously
processed environments, including decrypted credential material, persist on the node between runs. The runner is not
configured to clean the tree itself.

## Decision

We remove all untracked files from the working tree at the start of each run, after the tree is narrowed and checked
out and before any environment content is generated.

Rules:

- Scope is the whole working tree, not the current environment's paths, so leftovers of other environments are removed
  too.
- We remove untracked files and untracked directories, including any nested repository left by an interrupted parallel
  run.
- We preserve ignored files, because the node's ignored set can hold credential key material that must survive.
- We preserve repository metadata, so the fetched objects that keep fetch fast remain.

Rejected:

- Clean scoped to the current environment's paths, because it leaves other environments' artifacts on the node.
- Clean at the end of the run, because it adds cleanup-on-exit handling for only a node-disk gain that is not
  currently pressing.
- Clone fresh each run, because it discards the checkout-time saving that motivated fetch with sparse checkout.
- A sparse-aware cleanup limited to out-of-cone tracked directories, because it is unavailable in the runtime.

## Consequences

- Every run starts from a tree that holds only the checked-out commit plus ignored key material, so no other
  environment's artifacts or decrypted credential derivatives survive on the node.
- Node disk does not grow across runs.
- Downside: the current environment's own uncommitted leftovers from a crashed prior run are also removed, so a failed
  run leaves nothing recoverable on the node. Recovery comes from the artifact store or the repository.
- Downside: correctness depends on the cleanup preceding generation. A change that places a needed non-ignored file
  before checkout would have it removed.

See the preprocess step design in
[preprocess.md](/docs/technical-design/instance-pipeline/steps/preprocess.md).
