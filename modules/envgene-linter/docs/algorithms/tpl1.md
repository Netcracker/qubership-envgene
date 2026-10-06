# TPL-1: Jinja lives in template files

- [Repository and file selection](#repository-and-file-selection)
- [Descriptor fields](#descriptor-fields)
- [Source recognition](#source-recognition)
- [Output](#output)
- [Examples and verification](#examples-and-verification)

## Repository and file selection

Accept an EnvGene root with `templates/`, `environments/`, or both.
Run TPL-1, TPL-4, and TPL-6 on template-only repositories.
Mark other enabled rules Not applicable in console and HTML reports.
For mixed roots, retain the existing instance checks too.

Walk `templates/`, `environments/`, and `configuration/` recursively for `.yml`, `.yaml`, and `.j2` files.
This rule does not use Connections or require bindings. Unused files are eligible.
Skip directory symlinks and `.git`, `.venv`, `node_modules`, and `__pycache__` subdirectories.
Use the shared path safety check before reading file links. Other directories and root build metadata are outside scope.

Allow `.j2` files regardless of their directory. TPL-1 does not check template file placement.
For YAML, cache UTF-8 source text by physical path. Add a generic skip note on a read or decoding failure.
Analyze logical aliases separately to preserve their different descriptor roles.

## Descriptor fields

For files under `templates/env_templates/`, compose YAML nodes without evaluating Jinja or constructing tagged objects.
Recognize a descriptor by `tenant`, `cloud`, and a `namespaces` list.
A descriptor with `parent-templates` can inherit tenant and cloud. A tenant mapping can select a parent.

Collect source spans for scalar path values in `tenant`, `cloud`, `composite_structure`, `bg_domain`,
`external_credential_template`, `cloud.template_path`, and `namespaces[].template_path`.
Also collect scalar keys and values within `cloud.template_override` and `namespaces[].template_override`.
These are [generator-rendered fields](/scripts/build_env/render_config_env.py).
For composed cloud and namespace entries with a parent, also exempt `overrides-parent.name` and direct parameter maps
that composition transfers into `template_override`. A namespace without `template_path` can infer the sole parent.
Keep parameter-set lookup lists eligible.
Allow the schema-documented `namespaces[].name` selector syntax without treating it as a rendered field.
Only scalar path fields and mapping override bags qualify.

Exempt only delimiter pairs contained within these spans. Ignore YAML comments and keep unrelated fields eligible,
even on the same line. Do not exempt an alias anchor declared outside an allowed field.
Composition failures leave all matches eligible.

## Source recognition

1. Compose safe YAML nodes to validate syntax without constructing objects. Collect comment starts from YAML scanner tokens
   and handle block scalar header comments separately. Determine comment ends from physical source lines, stopping before
   active content. Token values can contain normalized whitespace and do not define source lengths.
   Mask comments with spaces while preserving newlines and offsets.
   If YAML composition or scanning fails, use a lexical source pass that tracks quotes, block scalar indentation,
   flow collections, scalar properties, continuation lines, and document markers.
   Keep complete Jinja constructs opaque within the current quoted scalar boundary.
2. Find the next opening delimiter in source order and search for its matching close:
   `{{`/`}}`, `{%`/`%}`, or `{#`/`#}`. Disable that family if no close remains.
3. Advance beyond a complete construct, ignoring nested openings inside it.
4. Omit constructs inside descriptor exemption spans.
5. Classify Jinja statement/comment delimiters as Fix.
   For expressions, remove quoted literals before classifying context names.
6. Classify expressions with known EnvGene context names as Fix unless downstream syntax is present.
   Shared delimiters without sufficient evidence, including Helm and application expressions, produce Review.
7. Map the opening offset to a line and column using the newline index.
   Keep one finding per physical file and line, preferring the first Fix over any Review on that line.

The scan includes malformed YAML, keys, metadata, quoted strings, and block scalars. YAML comments are excluded.
It does not validate the full Jinja grammar. Isolated delimiters and `${...}` macros are silent.
For exact context names and downstream syntax guards, see
[the specification and design](/modules/envgene-linter/docs/superpowers/specs/2026-09-28-tpl1-design.md).

## Output

Use Warning / Fix for confirmed Jinja candidates and Information / Review for ambiguous expressions.
Messages do not copy source values. Fix hints suggest concrete values, supported macros, or generator-processed templates.
Review hints recommend checking the downstream renderer. No rename, conversion, or template execution occurs.

Findings retain exit code 0 and are sorted by path, line, and column.
TPL-1 is enabled after VAL-4 by default. Disable it with `RULE_ENABLED["TPL-1"]` before building the package.
Disabled TPL-1 does not traverse or parse files. Shared instance discovery may still produce its own diagnostics.

## Examples and verification

The [positive example](/modules/envgene-linter/testdata/rules/tpl1/ok) uses an EnvGene macro in an instance ParameterSet
and Jinja in a template `.j2` file.
The [negative example](/modules/envgene-linter/testdata/rules/tpl1/not-ok) puts EnvGene Jinja in an instance YAML value
and a template YAML value. It produces two TPL-1 findings. These are linter fixtures, not complete generation inputs.

Run from `modules/envgene-linter` after installing the package:

```bash
envgene-linter check testdata/rules/tpl1/ok --console
envgene-linter check testdata/rules/tpl1/not-ok --console
```

- [Implementation](/modules/envgene-linter/src/envgene_linter/rules/tpl1.py)
- [Rule tests](/modules/envgene-linter/tests/test_tpl1.py)
- [YAML comment tests](/modules/envgene-linter/tests/test_tpl1_comments.py)
- [Repository and descriptor tests](/modules/envgene-linter/tests/test_tpl1_repository_scope.py)
- [Public example tests](/modules/envgene-linter/tests/test_rule_examples.py)
