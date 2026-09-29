# TPL-6: keep template logic small

- [Input and traversal](#input-and-traversal)
- [Classification](#classification)
- [Output and limits](#output-and-limits)
- [Examples](#examples)

## Input and traversal

Use [the shared template source selection](/modules/envgene-linter/docs/algorithms/tpl4.md#source-selection).
Walk the parsed Jinja statements and filters. Collect raw blocks separately from lexer tokens because
the abstract syntax tree represents raw contents as plain text.
Never execute a template or load an include, import, or parent template.

## Classification

1. Report `macro`, `include`, `import`, `from ... import`, `extends`, and `block` as Warning / Fix.
2. Allow `default`, its alias `d`, `join`, `upper`, and `lower`.
   Review other built-in filters. Report filters outside Jinja's built-in set as Warning / Fix.
3. Report loops over literal containers and literal `range(...)` arguments as Warning / Fix.
   Accept variable-based iterables as potentially dynamic. Review recursive loops.
4. Review statements outside the named simple subset, including assignments, calls with blocks, and filter blocks.
5. Allow raw blocks whose expressions are recognizable Helm syntax. Require a standard Helm context root
   or a Helm `include` call with a quoted name and a context argument as evidence. Allow associated flow controls and local variables.
   Review blocks with mixed expressions, plain text only, or unrecognized syntax.

Jinja comments and raw contents do not contribute executable statements or references.
See [the specification](/modules/envgene-linter/docs/superpowers/specs/2026-09-29-tpl6-design.md)
for the approved TPL-8 exception and exact interpretation boundaries.

## Output and limits

Report one finding per physical file, source line, and construct category, with column 1.
For descriptors, identify the selected scalar opening line. Fix takes precedence over Review within a category.
Use Warning / Fix for explicit prohibitions and Information / Review for uncertain cases.
Messages omit source values, custom names, and parser exception contents.
Read and parse failures produce generic skip notes. Other files remain eligible.

The rule does not impose a numeric nesting limit, resolve assigned iterable values, or validate Helm templates.
It performs no automatic rewrite. In particular, Review does not recommend removing a raw block.
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
```

Run the [positive fixture](/modules/envgene-linter/testdata/rules/tpl6/ok) and
[negative fixture](/modules/envgene-linter/testdata/rules/tpl6/not-ok) from `modules/envgene-linter`:

```bash
envgene-linter check testdata/rules/tpl6/ok --console
envgene-linter check testdata/rules/tpl6/not-ok --console
```

See [the implementation](/modules/envgene-linter/src/envgene_linter/rules/tpl6.py) and
[the tests](/modules/envgene-linter/tests/test_tpl6.py).
