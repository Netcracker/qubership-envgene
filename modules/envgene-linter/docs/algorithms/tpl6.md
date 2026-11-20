# TPL-6: keep template logic small

- [Input and traversal](#input-and-traversal)
- [Classification](#classification)
- [Output and limits](#output-and-limits)
- [Examples](#examples)

## Input and traversal

Use [the shared template source selection](/modules/envgene-linter/docs/algorithms/tpl4.md#source-selection).
Walk the parsed Jinja statements, including statements nested inside filter blocks.
The abstract syntax tree represents raw contents as plain text,
so no separate raw-content scan is needed.
Never execute a template or load an include, import, or parent template.
The separate [Ansible compatibility pass](/modules/envgene-linter/docs/algorithms/ansible-compatibility.md)
also inspects potential legacy expressions in additional configuration. Root GSF/CI description templates are excluded.

## Classification

1. Report `macro`, `include`, `import`, `from ... import`, `extends`, and `block` as Warning / Fix.
2. Allow every built-in and custom filter, including chained and dotted filter names.
   Allow `{% filter ... %}` blocks and continue checking their bodies.
   Review unavailable filters and statically unsupported arguments under the applicable rendering contract.
3. Report loops over literal containers and literal `range(...)` arguments as Warning / Fix.
   Accept variable-based iterables as potentially dynamic. Review recursive loops.
4. Review statements outside the named simple subset, including assignments and calls with blocks.
5. Allow every syntactically valid raw block without a style finding, regardless of its contents or downstream consumer.
   This includes application placeholders, Helm expressions, mixed syntax, plain text, and empty blocks.
   Review known compatibility transformations that alter literal raw content before Jinja processing.

Jinja comments and raw contents do not contribute executable statements or references.
See [the specification](/modules/envgene-linter/docs/superpowers/specs/2026-09-29-tpl6-design.md)
for the approved raw policy and exact interpretation boundaries.

## Output and limits

Report one finding per physical file, source line, and construct category, with column 1.
For descriptors, identify the selected scalar opening line. Fix takes precedence over Review within a category.
Use Warning / Fix for explicit prohibitions and Information / Review for uncertain cases.
Messages omit source values, custom names, and parser exception contents.
Read and parse failures, including unclosed raw blocks, produce generic skip diagnostics in
the [reports](/modules/envgene-linter/docs/algorithms/reports.md). Other files remain eligible.

The rule does not impose a numeric nesting limit, resolve assigned iterable values, or validate Helm templates.
It performs no automatic rewrite and does not validate text passed to downstream consumers.
Compatibility checks use the known renderer's filter registration and argument contract without executing filters.
They do not prove runtime input types or successful generation. TPL-4 still reviews unprotected filter inputs.
The rule is enabled by default and independently switchable.

## Examples

These template fragments demonstrate the classification:

```jinja
{# Fix: composition belongs outside an include statement. #}
{% include "shared.j2" %}
{# Allowed simple conditional. #}
{% if FEATURE_A | default(false) %}enabled{% else %}disabled{% endif %}
{# Allowed Helm passthrough. #}
{% raw %}{{ .Release.Name }}{% endraw %}
{# Allowed application placeholder. #}
{% raw %}{{ id }}{% endraw %}
{# Allowed registered EnvGene filter with protected input. #}
{{ FEATURE_A | default('') | to_nice_yaml }}
```

Run the [positive fixture](/modules/envgene-linter/testdata/rules/tpl6/ok) and
[negative fixture](/modules/envgene-linter/testdata/rules/tpl6/not-ok) from `modules/envgene-linter`:

```bash
envgene-linter check testdata/rules/tpl6/ok --console
envgene-linter check testdata/rules/tpl6/not-ok --console
```

See [the implementation](/modules/envgene-linter/src/envgene_linter/rules/tpl6.py) and
[the tests](/modules/envgene-linter/tests/test_tpl6.py).
