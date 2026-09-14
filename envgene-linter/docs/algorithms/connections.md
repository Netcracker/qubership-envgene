# Connected entities

Russian copy: [ru/connections.md](ru/connections.md).
Design: [connected-only scope](../superpowers/specs/2026-09-11-connected-only-design.md).

## Eligibility

All rules check only entities selected by visible local references or known
generator usage. NAME-3 also checks used environment definitions and their
cluster/environment directories; see [name3.md](name3.md) for namespace selection.
An unselected file contributes neither findings nor values, locations, categories,
or passport keys to another file's finding. Discovery may still index it and emit
read-error skip notes. Missing references are skipped, not diagnosed by a new rule.

| Entity | Evidence of use |
| --- | --- |
| ParameterSet | a surviving physical file from `resolve_reference(index, env, reference)` for a local deploy/e2e/technical binding |
| Cloud Passport | existing explicit `inventory.cloudPassport` resolution or documented automatic cluster passport selection |
| Resource Profile Override | `envSpecificResourceProfiles` with the existing level/directory priority |
| Shared credentials | `sharedMasterCredentialFiles` with the existing level/directory priority |
| Inventory generation credentials | exact `Inventory/credentials/inventory_generation_creds.yml` of a discovered environment |
| Shared Template Variables | `envTemplate.sharedTemplateVariables`, resolved by the local generator search described in [PLACE-10](place10.md) |
| Artifact Definition | `envTemplate.artifact`, `envTemplate.bgNsArtifacts.origin`, or `.peer` selects `configuration/artifact_definitions/<application>.yml` (then `.yaml`) |
| Application / Registry Definition | skipped: current local inputs do not prove which definitions the runtime Solution Descriptor selects |

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

AppDefs/RegDefs require a separate proven application selector (such as a supported
Solution Descriptor flow). Their directory presence, generated root copies, or
internal names do not establish usage. Current rules skip those records.

## PLACE-8 and reporting

PLACE-8 keeps Information / Review for known empty selected or used files.
Unselected, nonempty, unreadable, and unknown-structure files are silent.
Known fixed-path credentials may be absent without a finding; the generator uses
a default then. Alias matching and ambiguous first buckets retain PLACE-8's existing
behavior. PLACE-10 adds the thirteenth catalog header after PLACE-9 and before NAME-1.
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
