# VAL-4: complex values are native YAML

- [Inputs](#inputs)
- [Recognition](#recognition)
- [Output and limits](#output-and-limits)
- [Examples and verification](#examples-and-verification)

## Inputs

VAL-4 inspects strings in connected ParameterSets from `Connections.parameter_files`.
It walks `parameters` and `applications[].parameters`, including nested maps and lists, in all three parameter categories.
Selection uses the existing resolver before effective-value merging. Shared physical files are inspected once.
Unused and shadowed files do not become inputs to this rule.

Skip Jinja files, unreadable documents, and unsafe paths. The check does not inspect other entity types or metadata.
For the rationale and full contract, see
[the specification and design](/modules/envgene-linter/docs/superpowers/specs/2026-09-28-val4-design.md).

## Recognition

1. Walk each parameter bag iteratively. Track container ancestors to terminate cycles without hiding separate alias paths.
2. Skip non-string leaves and strings containing `${`, `{{`, `{%`, or `{#`.
3. For strings starting with `{` or `[` after trimming whitespace, attempt strict JSON decoding of the complete value.
   A map or list, including an empty collection, produces a candidate. Reject nonstandard JSON constants.
4. If JSON recognition fails, only literal or folded YAML block scalars remain eligible.
   Scan their decoded content for excessive token counts or depth and reject tags, directives, anchors, and aliases.
   Compose one YAML document without constructing objects and check collection depth in the resulting tree.
   A mapping or sequence node produces a candidate.
5. Ignore scalar results and parse errors. Do not parse ordinary quoted strings as general YAML.
6. Emit a finding at the source key or list item for each candidate and sort by file, line, column, and parameter path.

The rule checks structure recognition, not the consumer's required type.
A block scalar can contain text that happens to parse as a collection. Review is required before changing it.
A native collection can still contain nested serialized strings that produce their own findings.

## Output and limits

Findings use Warning / Review. Messages name the format and collection kind without copying encoded or decoded contents.
Parameter paths and file locations remain visible. The hint recommends native YAML if the consumer accepts structured data.
No conversion or file modification is performed. Findings retain exit code 0.

A candidate string is limited to 65,536 characters and 64 nested collections.
YAML block scanning allows at most 4,096 tokens. The outer parameter walk also limits nesting to 64 collections.
Each parameter bag allows at most 65,536 node visits, including repeated alias paths.
Exceeding a limit adds one generic skip note per file. Size and depth limits leave other eligible values reportable.
A visit limit stops the remaining traversal of that bag.
These limits do not change discovery or effective-set processing before VAL-4 runs.

VAL-4 is enabled by default after NAME-8. Disable it with `RULE_ENABLED["VAL-4"]` before building the package.
Disabled checks perform no VAL-4 parsing and produce no VAL-4 skip notes.

## Examples and verification

The [positive example](/modules/envgene-linter/testdata/rules/val4/ok) uses a native map and list.
The [negative example](/modules/envgene-linter/testdata/rules/val4/not-ok) contains a JSON string and a YAML block list.
The latter produces two VAL-4 findings. Other rules can report independent conditions.

Run these commands from `modules/envgene-linter` after installing the package:

```bash
envgene-linter check testdata/rules/val4/ok --console
envgene-linter check testdata/rules/val4/not-ok --console
```

- [Implementation](/modules/envgene-linter/src/envgene_linter/rules/val4.py)
- [Rule tests](/modules/envgene-linter/tests/test_val4.py)
- [Public example tests](/modules/envgene-linter/tests/test_rule_examples.py)
