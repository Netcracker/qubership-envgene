# Authored configuration and generated output

- [Default scope](#default-scope)
- [Path policy](#path-policy)
- [Reference context](#reference-context)
- [Processing and reports](#processing-and-reports)
- [Verification](#verification)

## Default scope

The default check targets authored configuration in instance and template repositories.
Generated Environment Instance files do not receive findings or incomplete-check diagnostics.
Each rule keeps its documented selection requirements within this common boundary.
The policy adds no coverage for previously unsupported sources.

## Path policy

`source_scope.is_generated_output(index, path)` recognizes full paths relative to an indexed environment.
Discovery identifies environments by `Inventory/env_definition.yml`.
The same policy checks logical paths and their resolved physical targets.
Filesystem confinement, symlink safety, and source eligibility are separate checks.

The following paths are relative to `environments/<cluster>/<environment>/`:

| Path                                   | Role                 |
|----------------------------------------|----------------------|
| `Applications/`                        | Generated objects    |
| `Namespaces/`                          | Generated objects    |
| `Profiles/`                            | Generated profiles   |
| `Credentials/`                         | Reference context    |
| `effective-set/`                       | Calculated output    |
| `cloud.yml`                            | Generated object     |
| `tenant.yml`                           | Generated object     |
| `bg_domain.yml`                        | Generated object     |
| `composite_structure.yml`              | Generated object     |
| `Inventory/namespace-map.yml`          | Pipeline output      |
| `Inventory/deploy-plan.yml`            | Pipeline output      |
| `Inventory/deploy-plan-calculated.yml` | Pipeline output      |
| `Inventory/deploy-plan-mapped.yml`     | Pipeline output      |

Directory entries exclude all descendants. Fixed file entries match only the named direct child.
Other paths retain their existing rule eligibility. In particular, `templates/.../Namespaces/`, cluster `Profiles/`,
and `Inventory/Credentials/` are not environment output directories.
An authored ParameterSet can contain a subdirectory named `Namespaces` or a file named `deploy-plan.yml`.
Generated-file comments do not suppress checks, and the policy does not depend on Git tracking or timestamps.

## Reference context

The generated Credential catalog can resolve an authored reference while remaining outside finding targets.
A missing catalog does not prove that an ID is missing because generation can supply it.
An unreadable catalog leaves the authored reference uncertain under INT-2's existing contract.
Available authoritative catalogs retain their existing existence and precedence semantics.
Context reads retain logical paths through aliases. A separate authored selection of the same physical
file retains its own checks and diagnostics.
SEC-5 checks protection in authored Credential sources and omits findings on generated catalog entries.
INT-4 retains generated objects as usage evidence for authored candidates.
This includes the supported nested Credential ID fields in rendered Cloud objects for MaaS, Vault, Consul, and DBaaS.

## Processing and reports

1. Establish environment output roots before loading authored entities.
   Preserve generated ParameterSet aliases as unavailable staging slots without parsing their contents.
   They cannot contribute to grouped content checks or restore shadowed lower sources.
   Prune generated directories from template and compatibility walks before reading their contents.
2. Apply authored-path eligibility to direct parameter and security checks.
   Keep explicit context reads available to reference and usage analysis.
3. Exclude generated paths when recording structured skips, including parser failures in context files.
   A context-dependent Review stays at its authored consumer.
4. Apply the shared location policy to findings returned by every rule as a final guard.
   Source selection excludes generated entries before grouping so authored group findings remain available.
5. Render the same selected findings in console, HTML, and JSON without adding excluded-file report entries.

The [generator cleanup list](/modules/envgene/envgenehelper/constants.py),
[namespace map writer](/scripts/build_env/namespace_render.py), and
[deployment plan writer](/scripts/deployment_plan/process_deployment_plan.py) define the supported output paths.

## Verification

The [regression tests](/modules/envgene-linter/tests/test_source_scope.py) compare all enabled rules before and after
adding generated files. They also exercise source controls, alias handling, reference context, and actual CLI reports.
The [design](/modules/envgene-linter/docs/superpowers/specs/2026-10-28-source-scope-design.md) records the contract.
