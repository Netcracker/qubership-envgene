# ADR-0002: Save the pipeline work directory as a troubleshooting artifact

Status: Proposed
Date: 2026-08-24

## Context

The consolidated instance-pipeline job produces intermediate and output files in its work directory. When
a run misbehaves an operator needs to inspect that state without rerunning it. Multi-environment runs fan
out to isolated worktrees that are torn down at the end, so their evidence is otherwise lost.

## Decision

We save the job work directory and the per-environment logs as a job artifact, on every run.

- A repository-wide `save_artifacts.strategy` (`ALWAYS` default, `NEVER`), overridable per run by
  `SAVE_ARTIFACTS_STRATEGY`, decides whether the work directory is saved. `NEVER` saves the logs only.
  `ALWAYS` is the default so evidence exists even for a run that looks green but produced wrong output.
- A size guard measures the uncompressed size of the work directory against `save_artifacts.size_limit_mb`
  (default 800 MB, which keeps the archived artifact under about 300 MB even at the worst-case 2.7x
  compression of encrypted credentials). Over it, EnvGene keeps only the logs and a `NOT-PUBLISHED.txt`,
  without failing the job. EnvGene does not compress the artifact: the runner archives the saved work
  directory as usual, so it stays browsable.
- The logs are small, so they are always saved, exempt from both the strategy and the size limit. As files
  they bypass the GitLab job log truncation (4 MB default, `ci_jobs_trace_size_limit`), which in a
  multi-environment run would otherwise leave no complete record of the console output.
- The SBOM retention total-size-limit default is lowered from 600 MB to 50 MB. At about 28 KB per SBOM that
  is roughly 1,800 files, a safety ceiling well above the roughly 7 MB a real `/sboms/` cache holds. SBOMs
  compress about 14x, so 50 MB is about 3.6 MB in the archive, near 1% of the roughly 300 MB archived
  artifact and 6% of the 800 MB uncompressed budget.

Rejected:

- `ON_FAILURE` strategy, because the size guard already bounds each artifact and `NEVER` opts out of the
  work directory, while a run that looks green can still produce wrong output that needs the artifact. A
  failure-only mode would only lose those cases.
- Outputs-only scope (env instance, Effective Set, deploy plan), because inputs such as templates and
  application definitions also aid troubleshooting.
- De-duplicating the shared layer into one copy, because application definitions, registry definitions and
  SBOMs are all mutated per environment, so the saving does not justify the complexity.
- Gating on environment count, because per-environment size varies roughly 200-fold, so a count is a false
  proxy for size.
- Compressing the artifact inside EnvGene to gate on the exact compressed size, because it adds a compression
  step and a store-mode runner setting, and makes the artifact an opaque blob the CI web UI cannot browse.

## Consequences

- Operators get the full run state and logs for any run, single- or multi-environment, without a rerun.
- We keep credential values in the artifact. A run that fails inside effective-set generation, before
  re-encryption, leaves them in plaintext. There is no requirement to remove them, replacing them with dummy
  values would add complexity, and troubleshooting needs the real values, so we accept this and document it as
  a security note.
- A multi-environment run whose work directory exceeds the 800 MB limit (roughly 150 or more credential-heavy
  environments) keeps only the logs and a `NOT-PUBLISHED.txt`.
- The implementation must stage each environment's work directory before its worktree is torn down.

See [Troubleshooting artifacts](/docs/features/troubleshooting-artifacts.md) and the pipeline flow
analysis for depth.
