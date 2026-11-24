# Shared ParameterSet sources

- [Problem and scope](#problem-and-scope)
- [Requirements](#requirements)
- [Design](#design)
- [Acceptance](#acceptance)

## Problem and scope

INT-2 can resolve a nested ParameterSet that discovery does not supply to content rules or the Effective Set.
JSON ParameterSets supported by the generator also need to reach these consumers.
This design closes that source-selection gap for the three instance layers.
It builds on the [connected-only contract](/modules/envgene-linter/docs/algorithms/connections.md).

Template composition, Jinja evaluation, generic parser hardening, and unrelated rule behavior are outside this change.

## Requirements

- Discover ordinary `.yml`, `.yaml`, and `.json` files recursively under the repository, cluster,
   and environment Inventory `parameters/` directories. Keep filename stems as reference names.
- Preserve relative directory paths during staging. A cluster file replaces a repository file at the same
   relative staged path. Environment inputs copy to `from_instance/` in the same staged tree and can replace
   repository or cluster files there. Different subdirectories and extensions remain distinct fragments.
- Use the same selected records for INT-2, Connections, Effective Set projections, and connected content rules.
   Resolve actual inputs before projection filtering. Do not restore shadowed files.
- Keep unbound files out of connected content checks. Retain indexed candidates for INT-4's separate analysis.
- Parse `.json` with Python's JSON decoder, preserving decoded types and generator-compatible duplicate-key behavior.
   Findings retain key locations, including nested and application parameters.
- Keep Jinja sources unrendered. A relevant unavailable source remains uncertainty rather than proof of a missing target.
- Exclude `.git`, external paths, and directory symlink traversal. Record incomplete scans so INT-2 cannot confirm
   complete resolution and PLACE-2 cannot prove removal using a partial source inventory.
- Change no CLI flags, report fields, rule defaults, dependencies, or source repository files.

## Design

### Source discovery and selection

`paramset_sources.py` owns recursive enumeration and reference selection.
Enumeration retains logical file paths, unavailable file markers, source directory layouts, and scan completeness.
Layouts include unsupported files because they can block a staged file's parent directory.
`discovery.py` loads the resulting records and stores each file's relative path under its parameter directory.
The index records parameter directories whose scan was incomplete.

Selection uses one staged-path map across all three copy phases. Unavailable files still replace lower-layer
files at the same path. An incomplete scan or file/directory collision suppresses connected selection because
the staged inputs are unknown. Application order follows the generator's staged-path tests, including its
`from_instance` substring test. Paths containing `from_template`, `from_origin_template`, or `from_peer_template`
require role-specific template context and make the affected reference uncertain in this implementation.
`effective.py` exposes its existing resolver import for compatibility,
while Connections and INT-2 use the shared selector directly.
INT-2 uses indexed records rather than independently scanning parameter directories.
Resource Profile and Credential lookup retain their existing separate contracts.

The generator references are
[copy_path](/modules/envgene/envgenehelper/file_helper.py),
[create_paramset_map and sort_paramsets_with_same_name](/scripts/build_env/build_env.py), and
[prepare_folders_for_rendering](/scripts/build_env/main.py).

### JSON values and positions

`yamlio.load()` dispatches `.json` to the JSON decoder. A token position tree supplies key locations
without replacing the JSON decoder's values with YAML coercions or string normalization.
Only the last occurrence of a duplicate key and its subtree supply values and positions.
`LoadedYaml.position()` supports the resulting position map as well as existing YAML line metadata.
JSON syntax errors become the existing read-error diagnostic. General unexpected parser failures are a separate task.

### Consumers and uncertainty

Connected rules receive nested and JSON ParameterSets through the existing Connections maps.
Effective Set replay and PLACE-2 removal analysis use the same selected records and source paths.
Incomplete directory scans prevent definitive reference and removal claims.
Known bindings in environments with incomplete selection remain potential consumers of shared sources.
They prevent a PLACE-2 Fix even when another environment can replay that source successfully.
INT-4's authored ParameterSet inventory and reference evidence reuse the shared enumeration so nested and JSON
sources are visible without making unbound files connected inputs. Its supplemental scan preserves candidates
in Inventory folders without an environment definition.

## Acceptance

- The same violation in a flat YAML, nested YAML, or JSON ParameterSet reaches its applicable content rule.
- Global and application parameters retain useful file, line, and column locations in reports.
- Same-named fragments in different subdirectories merge in staged-path order.
- Same relative repository/cluster paths shadow correctly, including unreadable shadowed sources.
- Environment copies replace colliding staged `from_instance/` paths.
- File/directory collisions and unsupported ancestor blockers cannot establish complete staging.
- A shared source cannot receive removal confirmation by excluding an environment with incomplete selection.
- Projections and PLACE-2 removal replay never restore shadowed files.
- Unbound and unsafe files supply no connected content findings.
- Missing, unreadable, Jinja, and incomplete-scan targets retain conservative INT-2 outcomes.
- HTML, JSON, and console reports carry findings from the added inputs using the existing schema.
