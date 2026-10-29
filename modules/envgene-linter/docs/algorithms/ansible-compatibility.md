# Ansible compatibility in TPL-6

- [Source contracts](#source-contracts)
- [Processing and checks](#processing-and-checks)
- [Findings and limits](#findings-and-limits)
- [Examples and verification](#examples-and-verification)

## Source contracts

[TPL-6](/modules/envgene-linter/docs/algorithms/tpl6.md) checks legacy-expression compatibility separately from its
statement restrictions. The collector preserves existing Jinja source spans and selects additional YAML or Jinja
under `templates/`, `environments/`, and `configuration/` when legacy markers occur.
Root `description_template*.yml` and `description_template*.yaml` are excluded as separate GSF/CI inputs.
Generated instance output is excluded by the [authored configuration scope](/modules/envgene-linter/docs/algorithms/source-scope.md).

Full YAML templates and ordinary template Registry/Application Definitions use the EnvGene contract.
All files with this confirmed full-renderer contract are analyzed, including expressions without Ansible names.
Bare ParameterSet `.j2` files and recognized ordinary descriptor path scalars use plain Jinja.
Cloud `template_override` mapping scalars use the EnvGene object renderer. Namespace overrides also pass through
an earlier custom Jinja renderer without replacements, so both contracts must support the expression.
Unconfirmed contexts remain unknown.
Valid additional ordinary YAML is decoded into scalar sources, with findings at each scalar's opening line.
Unreadable files produce generic skip diagnostics. Unsafe paths and `.git` targets are not read.

Physical aliases share analysis when their rendering contracts agree. An alias with a different consumer does not
inherit another consumer's compatibility result. TPL-4 and ordinary TPL-6 statement scope remain unchanged.

## Processing and checks

1. For the EnvGene contract, apply its three supported compatibility patterns to an analysis copy:
   the namespaced YAML filter, the exact single-quoted environment lookup, and standalone underscore names.
   Keep original line counts and source contents on disk unchanged.
2. Review transformations that alter literal data, raw contents, or a quoted Jinja string.
   Ignore changes confined to Jinja comments. YAML comments in full-file templates remain Jinja source.
3. Parse the processed copy without compiling or rendering. For TPL-6, a parse failure creates a located
   `Check skipped:` Review entry. Keep independent rewrite findings established before the failure.
   Standalone analyzer calls without a diagnostic callback retain a generic compatibility Review.
4. Traverse the AST iteratively. Review unresolved legacy calls and filters unavailable in the applicable renderer.
   Standard Jinja filters are available. The EnvGene renderer additionally registers `to_nice_yaml` and `urlsplit`.
5. Check these custom filter signatures without executing them. `to_nice_yaml` accepts no extra arguments.
   `urlsplit` accepts at most one `part` argument. Dynamic expansion and evidently invalid constant arguments
   produce Review. This is not a general runtime type analysis.
6. For unknown consumers, review legacy calls and nonstandard filters because their support is unconfirmed.
   Filter and raw syntax remains permitted. There is no blanket Ansible or custom-filter Fix.

The [design](/modules/envgene-linter/docs/superpowers/specs/2026-10-15-ansible-compatibility-design.md)
records the generator sources that define these contracts.

## Findings and limits

Emit one Information / Review per physical file and original line for compatibility issues.
Messages and recommendations omit source values, variable names, custom identifiers, lookup paths, and parser exceptions.
HTML, JSON, and console use the existing report schema. Disabling TPL-6 bypasses additional collection and analysis.

A compatible expression has no incompatibility found under the known contract. This does not prove successful rendering,
availability of every input, or correctness for an external consumer. TPL-4 separately reviews presence protection.
Descriptor analysis uses decoded scalar text. It does not reproduce whole-object serialization or prove that serialization
preserves every expression's quoting and escaping.
No lookup target, process environment value, plugin, external repository, or template dependency is read or executed.

## Examples and verification

These fragments illustrate compatibility, not complete generated objects:

```jinja
{# Compatible in the full EnvGene renderer. #}
{{ lookup('ansible.builtin.env', 'EXAMPLE') | default('') }}
{{ PARAMETERS | default({}) | ansible.builtin.to_nice_yaml }}
{# Review: this lookup form has no matching compatibility replacement. #}
{{ lookup("ansible.builtin.env", "EXAMPLE") | default("") }}
{# Review: the registered YAML serializer accepts no indent argument. #}
{{ PARAMETERS | default({}) | to_nice_yaml(indent=2) }}
```

Run the [compatible fixture](/modules/envgene-linter/testdata/compatibility/ansible/ok) or
[Review fixture](/modules/envgene-linter/testdata/compatibility/ansible/not-ok):

```bash
envgene-linter check testdata/compatibility/ansible/ok --console
envgene-linter check testdata/compatibility/ansible/not-ok --console
```

See the [pure analyzer tests](/modules/envgene-linter/tests/test_ansible_compat.py) and
[source and report tests](/modules/envgene-linter/tests/test_ansible_sources.py).
