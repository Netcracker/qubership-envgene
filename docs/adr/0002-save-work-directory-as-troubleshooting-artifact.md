# ADR-0002: Save the pipeline work directory as a troubleshooting artifact

Status: Proposed
Date: 2026-08-24

## Context

The consolidated instance-pipeline job produces intermediate and output files in its work directory. When
a run misbehaves an operator needs to inspect that state without rerunning it. Multi-environment runs fan
out to isolated worktrees that are torn down at the end, so their evidence is otherwise lost.

## Decision

We save the job work directory and the per-environment logs as a single `artifacts.tar.zst`, on every run.

- EnvGene compresses the archive with zstd itself. This measures the exact compressed size, and zstd is
  faster and tighter than the runner's zip. The runner is set to its lowest compression so it does not try to
  re-shrink the already-compressed archive, keeping its mandatory zip pass cheap.
- A repository-wide `save_artifacts.strategy` (`ALWAYS` default, `NEVER`), overridable per run by
  `SAVE_ARTIFACTS_STRATEGY`, decides whether the archive is saved. `ALWAYS` is the default so evidence exists
  even for a run that looks green but produced wrong output.
- A size guard compares the compressed archive to `save_artifacts.size_limit_mb` (default 100 MB, the GitLab
  default job artifact cap, so the stored archive is accepted as-is). Over it, EnvGene republishes the archive
  with only the logs and a `NOT-PUBLISHED.txt`, without failing the job.
- The logs are small, so they are exempt from the size limit and kept unless the strategy is `NEVER`. As files
  they bypass the GitLab job log truncation (4 MB default, `ci_jobs_trace_size_limit`), which in a
  multi-environment run would otherwise leave no complete record of the console output.
- To keep `/sboms/` a small share of the artifact, the SBOM retention total-size-limit default is lowered
  from 600 MB to 200 MB (about 14 MB compressed, near 14% of the artifact). That is a 3x cut from 600 that
  still caches enough to avoid frequent regeneration.

Rejected:

- `ON_FAILURE` strategy, because the size guard already bounds each artifact and `NEVER` covers opting out,
  while a run that looks green can still produce wrong output that needs the artifact. A failure-only mode
  would only lose those cases.
- Outputs-only scope (env instance, Effective Set, deploy plan), because inputs such as templates and
  application definitions also aid troubleshooting.
- De-duplicating the shared layer into one copy, because application definitions, registry definitions and
  SBOMs are all mutated per environment, so the saving does not justify the complexity.
- Gating on environment count, because per-environment size varies roughly 200-fold, so a count is a false
  proxy for size.
- Letting the CI runner archive the raw work directory, because it recompresses an already-large tree.
- Estimating the size from uncompressed bytes, because zstd measures the exact compressed size in about 3
  seconds worst case.

## Consequences

- Operators get the full run state and logs for any run, single- or multi-environment, without a rerun.
- We keep credential values in the artifact. A run that fails inside effective-set generation, before
  re-encryption, leaves them in plaintext. There is no requirement to remove them, replacing them with dummy
  values would add complexity, and troubleshooting needs the real values, so we accept this and document it as
  a security note.
- A multi-environment run whose compressed archive exceeds the 100 MB limit (roughly 60 or more
  credential-heavy environments) keeps only the logs and a `NOT-PUBLISHED.txt`. Accepted.
- The artifact is a single compressed archive, so the CI web UI cannot browse into it. Operators download and
  extract it to inspect. Accepted.
- The implementation must stage each environment's work directory before its worktree is torn down, and set
  the runner to its lowest compression so it does not re-shrink the archive.

See [Troubleshooting artifacts](/docs/features/troubleshooting-artifacts.md) and the pipeline flow
analysis for depth.
