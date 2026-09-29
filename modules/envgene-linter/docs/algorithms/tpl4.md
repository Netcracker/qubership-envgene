# TPL-4: protect potentially optional references

- [Source selection](#source-selection)
- [Presence analysis](#presence-analysis)
- [Output and limits](#output-and-limits)
- [Examples](#examples)

## Source selection

Walk `.j2` files under `templates/` and recognized environment template descriptors under `templates/env_templates/`.
Include unused template sources. Use the same safe file traversal as TPL-1, without following directory symlinks.
Do not read links outside the repository or into `.git`.

Select generator-rendered descriptor scalar fields using
[TPL-1's descriptor spans](/modules/envgene-linter/docs/algorithms/tpl1.md#descriptor-fields).
Exclude `namespaces[].name` selectors. Analyze scalars independently so one field cannot guard another.
Decode YAML scalars before parsing. Deduplicate physical source spans and parse with Jinja2 without compiling or rendering.
TPL-6 consumes the same parsed sources. If both rules are disabled, do not parse sources.

## Presence analysis

1. Walk statements in source order and maintain local names and exact paths known to be defined.
2. Treat a complete attribute or constant-key item access as one reference.
   Normalize `value.name` and `value['name']` to the same path.
3. Accept a direct reference wrapped by `default` or `d`. Check fallback arguments and dynamic indices separately.
   Visit inputs of arithmetic, calls, and preceding filters even if their result has a default.
4. Accept direct presence tests. Propagate exact-path facts into the appropriate `if`, `elif`, `else`,
   conditional-expression, and short-circuit branches.
5. Bind loop targets within the loop body and assigned names after their assignment.
   Preserve macro, `call`, `filter`, and `with` scopes. Remove stale guard facts when a name is possibly rebound.
   Loop filters use outer loop metadata, while loop bodies receive their own metadata.
6. Recognize Jinja globals, standard loop properties, and the limited generator guarantees in
   [the specification](/modules/envgene-linter/docs/superpowers/specs/2026-09-29-tpl4-design.md#presence-protection).
7. Record other reads as review candidates. A defined parent or a bound local name does not guarantee its attributes.

## Output and limits

Emit one Information / Review finding per physical file and line, at column 1.
For descriptors, identify the selected scalar opening line because YAML quoting and folding can change line counts.
Messages do not include source names or values. The finding states that presence protection was not recognized,
not that generation necessarily fails. Read and syntax failures produce generic skip notes.

The rule does not inspect remote inputs, infer types, or prove arbitrary data flow.
It does not render templates, recommend a business default, or change the checked source.
It is enabled by default and supports the shared CLI and HTML reports.

## Examples

These expression fragments illustrate presence protection, not complete EnvGene objects:

```jinja
{# Review: input availability is unknown. #}
{{ FEATURE_A }}
{# Protected read. #}
{{ FEATURE_A | default('') }}
{# Review: the addition happens before the default. #}
{{ (COUNT + 1) | default(0) }}
{# Protected input to the addition. #}
{{ (COUNT | default(0)) + 1 }}
```

Run the [positive fixture](/modules/envgene-linter/testdata/rules/tpl4/ok) and
[negative fixture](/modules/envgene-linter/testdata/rules/tpl4/not-ok) from `modules/envgene-linter`:

```bash
envgene-linter check testdata/rules/tpl4/ok --console
envgene-linter check testdata/rules/tpl4/not-ok --console
```

See [the implementation](/modules/envgene-linter/src/envgene_linter/rules/tpl4.py) and
[the tests](/modules/envgene-linter/tests/test_tpl4.py).
