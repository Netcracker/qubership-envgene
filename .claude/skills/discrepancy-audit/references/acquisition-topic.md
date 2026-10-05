# Acquisition - topic mode

This file describes phases 1 and 2 of the audit harness for the topic-scoped mode. Phases 3, 4,
and 5 (truth location, verdict assignment, and report) are governed by `references/verify-before-claim.md`,
`references/verdict-model.md`, and `references/report-format.md` respectively, and are shared
across all modes.

## Phase 1 - scope resolution

Turn the topic into a concrete corpus before any claim extraction begins. The corpus has three
parts: a list of docs, a list of code entry points, and a list of relevant schemas.

**Wide topics** (a feature area, an object type, a pipeline stage): fan out `Explore` agents to
gather candidates across `docs/`, `scripts/`, `modules/`, `schemas/`, and `build_effective_set_generator/`.
Return candidates as a list, not as pre-read content.

**Narrow topics** (a single parameter, a single config key): use an inline glob or grep to locate
the relevant files directly without fan-out.

The corpus is shown to the user before any auditing starts. Boundaries are editable at that point.
Do not proceed to phase 2 until the user confirms or adjusts the corpus. This confirmation gate
exists because a missed doc or an extra doc changes which claims are extracted and which
contradictions are visible. The primary corpus is user-facing documentation under `docs/`. Internal
developer docs such as `CLAUDE.md` files may be included as a secondary source, but findings
against them are flagged as internal-doc, not user-facing.

### Worked example - "cert handling"

Topic: how EnvGene handles SSL certificates.

Corpus assembled from a narrow grep and directory scan:

- Docs: `docs/how-to/configure-system-certificates.md`, `docs/features/system-certificate.md`
- Code entry point: `scripts/utils/handle_certs.sh`
- Schema: none (shell script, no JSON schema)

The user confirms this corpus (or adds `configuration/config.yml` if cert-backend config is in
scope). Phase 2 then extracts claims from the two doc files against the shell script.

## Phase 2 - claim extraction

From the confirmed corpus docs, pull every checkable claim. A checkable claim names a concrete,
verifiable fact about the system. Pure conceptual prose that makes no falsifiable assertion becomes
`unverifiable` and is carried in the report with that verdict, not dropped.

The EnvGene claim taxonomy - the kinds of claims worth extracting:

- **Identifiers** - parameter names, environment variable names, YAML field names, kind values,
  enum values.
- **Defaults** - the default value stated for a parameter or config field.
- **Enum values** - the full set of allowed values and what each does.
- **Contract parameters** - inputs and outputs of a pipeline step, calculator CLI argument names,
  and flags.
- **Behavior** - what the pipeline does in a given condition (for example, "skips provisioning
  when `EXTERNAL_CREDENTIAL_PROVISIONING=skip`").
- **Artifact producer/consumer pairs** - which step writes a file and which step reads it (for
  example, "the SBOM downloader writes `dd.zip`, the effective-set generator reads it").

For each extracted claim, record the source doc and line number. That record becomes the "doc
quote" half of the evidence pair required in phase 4.
