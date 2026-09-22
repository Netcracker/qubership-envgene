# NAME-2

- [NAME-2](#name-2)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

NAME-2 compares a connected file's filename stem with its root `name` field.
The filename stem is the reference key. A mismatch produces Warning / Fix;
a missing name produces Information / Review. The rule recommends setting
`name` and does not edit or rename files. No Effective Set merge is needed.

## Input parameters

These are inputs to `check(index, connections=None)`, not additional CLI options.

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `index` | Rule argument from repository discovery | Yes | None | `RepoIndex` with ParameterSets, named entities and bindings | Supplies filename stems, root YAML and key positions |
| `connections` | Optional rule argument / shared resolver | No | `compute_connections(index)` | `Connections.parameter_files` and `artifact_definitions` | Selects the records eligible for comparison |

## Processing flow

1. **Select connected files**

   1. Reuse `connections`, or compute it from `index` when omitted.
   2. Take ParameterSets from `connections.parameter_files`, keeping the actual
      selected records and deduplicating physical paths.
   3. Take `index.named_entities` records whose resolved paths occur in
      `connections.artifact_definitions`. Shared selection resolves literal
      `envTemplate.artifact`, `envTemplate.bgNsArtifacts.origin` and `.peer`
      references by application filename, preferring `.yml` to `.yaml`.
   4. Exclude orphan files and Application/Registry Definitions whose local use
      is unproven. Skip Jinja, load errors and records without loaded YAML.

2. **Read the declared name**

   1. Use the indexed stem produced by `paramset_stem`, which strips `.j2`
      before the data extension.
   2. Read `name` only from a root mapping. A non-mapping root, absent key,
      null value or `""` means the name is missing.
   3. For every other value, use Python `str(value)` without trimming or
      case normalization. For example, integer `1` becomes `"1"`.

3. **Compare and create a finding**

   1. For a missing name, emit Information / Review. Use the `name` key's YAML
      position if present, otherwise `1:1`.
   2. For a usable name equal to the stem, emit nothing.
   3. For a usable name unequal to the stem, emit Warning / Fix at the `name` key.
   4. Use `kind=ParameterSet` or `kind=Artifact definition`, the selected record's
      path, `key=name`, `scope=stem`, one location and empty `related`.

4. **Return ordered findings**

   1. Sort by path, key and line. Each checked record contributes at most one finding.

## Result

The result is a list of `NAME-2` findings with these exact diagnostic templates:

| Case | Severity / type / action | Message | Hint |
| --- | --- | --- | --- |
| Mismatch | `warning` / Warning / Fix | `{kind} filename stem {stem!r} does not equal the name field {declared!r}.` | `Set name: {stem} to match the filename, which is the reference key.` |
| Missing name | `information` / Information / Review | `{kind} {filename} has no name field; EnvGene requires it to equal the filename stem {stem!r}.` | `Set name: {stem}` |

`filename` is the basename including its extension. The catalog description is
`Filename stem must equal the name field`. Console output includes the location,
severity, message and hint; HTML shows that location and the finding's type/action.
An empty block is `NAME-2` followed by `No findings`.

## Error handling

**1a.** Unresolved references and unproven runtime selection produce no NAME-2
finding; discovery may still report read-error skip notes.

**1b.** A selected malformed `.yml` Artifact Definition retains priority over
`.yaml`, but its load error causes it to be skipped. NAME-2 does not retry the
lower-priority file.

**2a.** Missing, empty or null `name` is handled by step 3.1, not as a mismatch.
A successfully loaded non-mapping root follows the same missing-name branch.

## Example

Assume a binding selects `cloud-deploy.yml`:

```yaml
name: deploy-params
parameters: {}
```

One Warning / Fix finding points to `name` and has `scope=cloud-deploy`:

```text
ParameterSet filename stem 'cloud-deploy' does not equal the name field 'deploy-params'.
Set name: cloud-deploy to match the filename, which is the reference key.
```

Setting `name: cloud-deploy` removes this finding. Removing `name`, or setting
it to null or `""`, produces one Information / Review finding with hint
`Set name: cloud-deploy`. An unbound copy or a Jinja file produces none.

## Related documentation

- [Russian version](ru/name2.md)
- [Connected entities](connections.md)
- [Rule implementation](../../src/envgene_linter/rules/name2.py)
- [Rule tests](../../tests/test_name2.py)
- [Connection resolver](../../src/envgene_linter/connections.py)
- [Reporting](../../src/envgene_linter/report.py)
