# ADR-0001: Adapt registry auth parameters into per-downloader auth for EnvGene

Status: Accepted
Date: 2026-08-20

## Context

EnvGene downloads Maven artifacts (SD, DD, SBOM inputs) for effective set generation and needs registry auth
for public cloud and non-public registries. The same auth is already authored as registry auth parameters
(`PUB_REG_*` and `NON_PUB_REG_*`) for the rest of the DevOps toolset. Requiring operators to also author a
RegDef v2 `authConfig` for EnvGene would make them enter it twice. EnvGene's two download paths differ. The
artifact-searcher path already consumes a RegDef v2 `authConfig`, while the dpg path was stubbed and did no
auth.

## Decision

We add a transitional adapter step after `appregdef_render`. It resolves the registry auth parameters once
(render the Cloud object in memory, expand credential macros) and feeds each downloader in the form its
library consumes natively:

- **dpg** gets a transient file of the resolved parameters. dpg reads it and builds its runtime registry
  object.
- **artifact-searcher** gets a synthesized RegDef v2 that reuses the v1 RegDef's Maven coordinates and adds an
  `authConfig` that each registry section references by name. That `authConfig` carries a `credentialsId`. The
  step creates that credential in memory from the resolved key and secret and merges it into the decrypted
  credentials the resolver reads for the run.

None of these outputs is committed. The downloaders read them from outside the committed instance repository,
so the committed RegDefs stay at v1 for consumers that do not read v2 and the committed credential store is
untouched. The RegDef v2 is synthesized only for public cloud registries that are not already at
`version: "2.0"`. The step synthesizes it for `MAVEN_PROVIDER` `aws` and `gcp`. A `nexus` or `artifactory`
registry keeps its RegDef v1. For `azure`, the dpg path authenticates from the parameter file, but RegDef v2
synthesis for the artifact-searcher path is planned and not implemented yet. The env template download
authenticates through its Artifact Definition, the Java calculator reads committed coordinates and needs no
auth, and `generate_argocd_repo` reads a local cache, so none is a consumer. We remove the adapter once the
registry auth parameters are retired in favor of RegDef v2.

Rejected:

- Teach the rest of the toolset to read RegDef v2 now, because that is a large multi-team change outside
  EnvGene and does not remove the parameters operators already maintain.
- Keep operators authoring both the parameters and a RegDef v2, because removing that double authoring is the
  point of this decision.
- Feed one uniform object to both paths, because dpg and artifact-searcher consume different native shapes, a
  flat parameter file versus a RegDef v2.
- Gate the step with a feature flag, because the pipeline run condition and the `MAVEN_PROVIDER` provider
  already decide when it synthesizes, and a disabled flag with the parameters set would only break the
  download.

## Consequences

- Operators author registry auth once, and EnvGene authenticates to public cloud and non-public registries
  with no duplicate entry.
- The adapter is transitional and disposable, removed once RegDef v2 is authored directly.
- The adapter must expand credential macros itself, because `create_credentials` runs later. This adds a
  dependency on credentials being decrypted at that point.
- Auth values cannot depend on `solution_structure`, because the early Cloud render precedes SD processing.
- The auth is global, one per instance, applied to every Maven registry, because EnvGene downloads only
  Maven and `MAVEN_PROVIDER` is a single value. This assumes a single Maven registry type per instance.
- The adapter's outputs are not committed. The parameter file and the RegDef v2 live in a transient
  directory, and the credential is held in memory for the run. The cost is that the downloaders depend on
  those transient outputs for the run.
- The adapter writes the parameter file and sets `LOCAL_PUBREG_FILE` to its path. dpg reads the file from
  there.
