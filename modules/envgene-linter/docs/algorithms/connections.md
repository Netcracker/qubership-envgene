# Connected entities

Russian copy: [ru/connections.md](ru/connections.md).
Design: [connected-only scope](../superpowers/specs/2026-09-11-connected-only-design.md).

## Eligibility

All rules check only entities selected by visible local references or known
generator usage. NAME-3 also checks used environment definitions and their
cluster/environment directories; see [name3.md](name3.md) for namespace selection.
An unselected file contributes neither findings nor values, locations, categories,
or passport keys to another file's finding. Discovery may still index it and emit
read-error skip notes. The legacy graph skips unresolved references; [INT-2](int2.md) separately diagnoses supported missing/ambiguous targets or unavailable context.

| Entity | Evidence of use |
| --- | --- |
| ParameterSet | a surviving physical file from `resolve_reference(index, env, reference)` for a local deploy/e2e/technical binding |
| Cloud Passport | existing explicit `inventory.cloudPassport` resolution or documented automatic cluster passport selection |
| Resource Profile Override | `envSpecificResourceProfiles` with the existing level/directory priority |
| Shared credentials | `sharedMasterCredentialFiles` with the existing level/directory priority |
| Inventory generation credentials | exact `Inventory/credentials/inventory_generation_creds.yml` of a discovered environment |
| Shared Template Variables | `envTemplate.sharedTemplateVariables`, resolved by the local generator search described in [PLACE-10](place10.md) |
| Artifact Definition | `envTemplate.artifact`, `envTemplate.bgNsArtifacts.origin`, or `.peer` selects `configuration/artifact_definitions/<application>.yml` (then `.yaml`) |
| Application / Registry Definition | skipped by the legacy graph; SEC-5 separately follows active legacy registry consumers and registry Credential references in selected Artifact Definitions |

Names are not globally unique identities. Deduplicate resolved physical paths and
retain the environment, target, reference and category of each actual use. A
same-named file in an unrelated cluster is not selected. A malformed selected file
still occupies its resolution slot, but content checks skip unreadable documents.
Jinja and external/template/runtime-only references are not rendered or inferred.

## ParameterSet projections and naming

Resolve full-layer inputs first. Cluster replacement by the same staged filename
removes a repository file from that environment's selected inputs. For `full`,
`lower`, and `site`, filter those actual inputs to the requested layers before
merging. A projection never brings back a shadowed file.

NAME-1 and NAME-2 inspect selected files only. NAME-4 groups categories by physical
file and uses cluster/environment identifiers only from that file's actual users.
Different physical files with equal stems do not share naming requirements.
PLACE-6 ignores a target without any resolved ParameterSet. PLACE-7 ignores
unresolved references and preserves original list positions for resolved conflicts.
Both keep their existing messages for actual connected inputs.

Passport catalogs retain the static contract table and keys from selected
passports only. An unused cluster passport cannot suppress PLACE-1 through its keys.
PLACE-3 checks the placement of selected passports; PLACE-4 checks selected
ParameterSets, without reparsing unrendered Jinja as plain YAML.

## Artifact lookup and limits

Artifact selectors must be literal strings with nonempty first two colon-separated
components (`application:version`). As in the generator, later components do not
change the application component. Placeholder-looking values, malformed containers,
legacy `templateArtifact` GAV input, and unavailable runtime overrides are skipped.
Lookup is by filename, not the document's `name`; NAME-2 then compares `name` with
the selected filename. A malformed `.yml` still takes priority over `.yaml`.
The artifact's embedded `registry` object is not a reference to a RegDef.

AppDefs/RegDefs require a proven consumer. Their directory presence, generated root
copies, or internal names do not establish usage. The legacy connection graph skips
those records. SEC-5 separately follows an active legacy registry consumer and a
`registry.credentialsId` in a selected Artifact Definition; this does not select
other definitions or change eligibility for existing rules.

## SEC-5 security sources

SEC-5 builds distinct source records alongside `Connections`; it does not add them
to legacy credential sets. Records retain source kind, physical path and environment.
Whole-file sources and entry-level consumers remain distinct so that a system
reference does not make every entry in a root Credential catalog eligible.

In addition to selected shared Credentials and the exact Inventory-generation file,
SEC-5 selects each discovered environment's existing generated
`Credentials/credentials.yml`, the first known companion of a uniquely selected
Cloud Passport, and ordinary connected ParameterSet and Cloud/Namespace parameter
maps. It also follows the bound deployer entry and its selected companion, documented
system integration/root-credentials references, active legacy registry consumers,
and `registry.credentialsId` from selected Artifact Definitions.

Passport companion priority is `credentials/<passport-stem>.yml`, then the adjacent
`<passport-stem>-creds.yml`. Deployer resolution requires `inventory.deployer` and
uses the generator's cluster-before-environment, app-before-cloud and basename order;
the fallback `configuration/deployer.yml` applies only when the selected definition
lacks the requested entry. An unsafe or unreadable first-priority candidate blocks
fallback. References resolve only within their selected catalog. Runtime parameters
use the generated environment catalog when it exists; SEC-5 does not guess a merge
across shared catalogs when it does not.

An absent integration `self_token` is the documented automatic CI lookup and is
silent. An explicit value is inspected. Inactive registries, unused deployer
definitions, arbitrary CI workflow files, unrelated passport companions, historical
copies and Effective Set outputs remain outside SEC-5's source records.

## SEC-4 pair consumers

SEC-4 reuses connected security bags to find sibling user/password parameters with matching prefixes and supported suffixes. It compares literal Credential IDs in both references without reading or resolving Credential catalogs. Different IDs produce Information / Review; absent definitions and incomplete blocks are outside SEC-4. Pairs never cross environments, applications, mappings or list elements.

## INT-2 reference consumers

INT-2 reuses connected security bags and selected Cloud/Namespace objects. Explicit ParameterSet or Resource Profile binding targets also select an existing namespace consumer even when its bound target is unavailable. This scope is local to INT-2. It checks Credential object existence, ParameterSet bindings/lists and Resource Profile references using their applicable catalogs, staging and directory priorities. Definite missing/ambiguous targets produce Warning / Fix; dynamic, unreadable or unavailable template context produces Information / Review. See [INT-2](int2.md) for generated-catalog authority, ordered shared overrides and generated Profiles lookup.

## PLACE-8 and reporting

PLACE-8 keeps Information / Review for known empty selected or used files.
Unselected, nonempty, unreadable, and unknown-structure files are silent.
Known fixed-path credentials may be absent without a finding; the generator uses
a default then. Alias matching and ambiguous first buckets retain PLACE-8's existing
behavior. PLACE-10 follows PLACE-9; SEC-1 follows PLACE-10; SEC-3 follows SEC-1;
SEC-4 follows SEC-3; SEC-5 follows SEC-4; INT-2 follows SEC-5 and precedes NAME-1. The console has
eighteen rule headers.
There are no new CLI flags, other severity changes, autofix, or network calls.

## Examples

An unreferenced `parameters/unused.yml` is silent even if its name is wrong or its
keys would otherwise trigger NAME-1/2 or PLACE-4. Adding a binding to its exact stem
makes the physical file eligible for the appropriate checks.

In two clusters, `service-deploy.yml` used as deploy in the first cluster and e2e
in the second produces a NAME-4 category-tail finding only for the second file.
A dangling e2e reference in the second cluster cannot change the first file's category.

Run the synthetic fixtures with `.venv/bin/envgene-linter check testdata/place8/not-ok`
and `testdata/place8/ok`: three bound empty entities produce three PLACE-8 findings;
three unbound empty entities produce none.

## Passport resolution conflicts

[PLACE-9](place9.md) also checks ambiguous candidates reached by a used passport reference or automatic lookup. Such candidates are not selected for other content rules. It also checks the first existing known passport-credentials companion without inspecting its contents. Missing and unused files remain silent.

## Shared Template Variables

Explicit `envTemplate.sharedTemplateVariables` bindings now select Shared Template Variable files using the local generator lookup. These physical paths participate in global and per-environment selection. [PLACE-10](place10.md) checks their type directory along with ParameterSets, profiles, shared credentials and passports. Selection does not infer types from arbitrary YAML.
