# Authored configuration scope

- [Contract](#contract)
- [Approaches](#approaches)
- [Path classification](#path-classification)
- [Reference context](#reference-context)
- [Verification](#verification)

## Contract

The default check reports findings against authored configuration in instance and template repositories.
Generated Environment Instance objects and pipeline outputs are outside that scope, including incomplete-check
diagnostics against those files. This implements the shared source-selection approach accepted on October 28, 2026.
No additional rule, command option, dependency, report field, or automatic configuration edit is introduced.

Source selection applies before content checks. The engine also enforces the same location boundary across all rules.
Unknown paths retain their existing eligibility. A comment claiming that a file is generated does not suppress checks.
The implementation does not infer one build state for an entire repository.

## Approaches

The accepted approach uses one path policy shared by readers, diagnostics, and the engine.
Filtering only rendered reports would still inspect excluded files and leave direct rule calls inconsistent.
Separate exclusion lists in individual rules would allow their scope to diverge.

## Path classification

A known environment is an environment discovered through `Inventory/env_definition.yml`.
Within its root, the following directories are generated outputs: `Applications/`, `Namespaces/`, `Profiles/`,
`Credentials/`, and `effective-set/`. The generated files are `cloud.yml`, `tenant.yml`, `bg_domain.yml`, and
`composite_structure.yml`.

The generated files directly inside `Inventory/` are `namespace-map.yml`, `deploy-plan.yml`,
`deploy-plan-calculated.yml`, and `deploy-plan-mapped.yml`.
Nested files with those names in authored entity directories keep their existing scope.

Classification uses the full environment-relative path. Template Repository `Namespaces/`, cluster `Profiles/`,
and `Inventory/Credentials/` remain eligible under their existing contracts.
Logical paths and resolved paths both participate so an alias cannot expose a generated file as an authored target.
The existing repository-confinement and symlink rules remain in force.

## Reference context

Generated files can supply evidence for an authored reference without becoming finding targets.
In particular, `Credentials/credentials.yml` remains available to resolve Credential IDs and reference shape.
The implementation treats this persistent catalog as context only because EnvGene also updates it during generation.
Shared and system Credential source files retain their existing secret-protection checks.

Unavailable or invalid context retains conservative handling at the authored consumer.
It does not create a confirmed missing-reference finding merely because generation has not run.
Generated-catalog parser diagnostics do not appear as checks against that catalog.
INT-4 can still use rendered references as usage evidence without diagnosing generated entities as unused.

## Verification

Real synthetic repositories exercise every enabled rule before and after adding generated files.
The source-only results remain identical when those outputs add no evidence for an authored reference.
Separate tests cover generated Credential catalogs as valid, missing, and malformed reference context.
HTML, JSON, and console output contain no findings or incomplete-check locations against generated files.
Control cases cover template Namespaces, legacy authored directories, nested ParameterSets, and unknown source paths.
The full module suite and applicable Python and Markdown linters run after implementation.
The three baseline macOS Credential casing failures remain outside this change.
