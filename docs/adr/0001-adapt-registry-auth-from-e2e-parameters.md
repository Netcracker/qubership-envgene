# ADR-0001: Generate RegDef v2 on the fly from RegDef v1 and pub_reg parameters

Status: Proposed
Date: 2026-08-20

## Context

EnvGene supports the new RegDef v2, but the rest of the DevOps toolset (deployer, ArgoCD, builder) does not
yet. Those components read registry auth from the legacy pub_reg parameters in the pipeline context. Until
they support v2, requiring both a RegDef v2 `authConfig` for EnvGene and the pub_reg parameters for everyone
else would force operators to author the same auth twice.

## Decision

We add a temporary adapter step after `appregdef_render` that assembles a runtime `RegistryInfo` object in
memory, the resolved form of a RegDef v2 and not a RegDef v2 file: the committed RegDef v1 coordinates plus
an `authConfig` synthesized from the resolved pub_reg parameters (`PUB_REG_*`). It
renders the Cloud object, folds paramsets into parameters, reads the whole `e2eParameters` section,
expands its credential macros to resolve secret values, and takes the pub_reg parameters it needs. The whole
object stays in memory and is never saved in the repository. The Java calculator is not a consumer, because
it reads committed coordinates and needs no auth. The per-step consumer map is below.

The transform is gated in two levels. A `configuration/config.yml` feature flag is the master switch, default
off. When on, a per-registry pub_reg discriminator triggers it. A committed RegDef already at
`version: "2.0"` is passed through. We remove the adapter once the rest of the toolset supports RegDef v2.

Consumers do not choose between the RegDef and `ctx`. They all resolve through the single `get_registry_info`
seam, which returns the synthesized `RegistryInfo` for the run in place of the on-disk stub:

- `process_sd`, `run_generate_deployment_plan`, and `get_sboms` read the synthesized `RegistryInfo` through
  the shared dpg download path.
- `process_env_template` (env template) is out of scope and authenticates through its Artifact Definition v2.
- `generate_argocd_repo` performs no download and reads the local DD cache from `dd_downloading`.

Rejected:

- Teach the rest of the toolset to read RegDef v2 now, because that is a large multi-team change outside
  EnvGene and is the end state this adapter bridges toward, not something available during the transition.
- Keep operators authoring both the pub_reg parameters and a RegDef v2, because removing that double
  authoring is the point of this decision.
- Produce only an in-memory `authConfig` overlay on the v1 RegDef, because a full v2 object lets every
  downloader read one uniform shape.

## Consequences

- Operators author registry auth once, as pub_reg parameters, during the transition, and RegDef v2 works for
  EnvGene with no duplicate entry.
- The adapter is flag-gated and disposable. It carries throwaway code until the toolset supports v2, at which
  point it and the flag are removed.
- The adapter must expand credential macros itself, because `create_credentials` runs later. This adds a
  dependency on credentials being decrypted at that point.
- Auth values cannot depend on `solution_structure`, because the early Cloud render precedes SD processing.
