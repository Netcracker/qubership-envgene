# NAME-1

- [NAME-1](#name-1)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

NAME-1 identifies different parameter names with exactly equal non-empty string
values in connected ParameterSets. Equality is a review candidate, not proof of
an alias. Every finding is Information / Review; files and keys are not changed.
The rule reads selected records without merging an Effective Set.

## Input parameters

These are inputs to `check(index, connections=None)`, not additional CLI options.

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `index` | Rule argument from repository discovery | Yes | None | `RepoIndex` with ParameterSet records and environment bindings | Supplies selected YAML content and key positions |
| `connections` | Optional rule argument / shared resolver | No | `compute_connections(index)` | `Connections.parameter_files` keyed by physical path | Restricts value groups to actual selected ParameterSets |

## Processing flow

1. **Select ParameterSet records**

   1. Reuse `connections`, or call `compute_connections(index)` when omitted.
   2. Read `connections.parameter_files`: selected repository, cluster and
      environment files, deduplicated by resolved physical path. Keep each selected
      record's path and name; an unused alias cannot replace them.
   3. Skip Jinja, records with `error`, and records with `loaded is None`.
      Other YAML types, orphan files and shadowed files do not contribute.

2. **Collect named string leaves**

   1. Walk nested mappings in `parameters` at any depth with `yamlio.leaves`.
      Keep only strings other than `""`; do not descend into lists. Numbers,
      booleans and null values do not contribute.
   2. Use the complete dotted path as the key identity. Thus `outer.KAFKA_URL`
      and `KAFKA_URL` are different names.
   3. If `applications` is a list, inspect its mapping entries. Resolve the
      application name as `entry.get("appName") or entry.get("name")`; require
      a truthy result and a mapping `parameters` value. Repeat the leaf collection
      for each eligible `applications[i].parameters`, prefixing each key with
      the resolved name converted to a string and `.`. Retain the file and YAML
      key position for every occurrence.

3. **Group values and remove credential pairs**

   1. Group all occurrences by exact string value across selected files.
   2. Build the set of distinct full key names in each group.
   3. Compare the final dotted segment case-insensitively. For every segment
      ending in `_USER` or `_USERNAME`, look for the same prefix followed by
      `_PASSWORD` or `_PASS` in another name. Dotted parents need not match.
   4. Remove both sides of every matching pair simultaneously. Retain the group
      only when at least two distinct names remain; repeated occurrences of one
      name are insufficient.

4. **Create and order findings**

   1. Keep all occurrences of remaining names and sort by file path, then key.
      Use the first occurrence as the primary path, position and key.
   2. Emit one finding per retained value group, including every retained
      occurrence in `locations` and sorted unique names in `related`.
   3. Sort findings by path, key and line before returning them.

## Result

The result is a list of `NAME-1` findings with `severity=information`,
`issue_type=Information`, `action=Review` and `scope=repository`.

- Message: `Keys {sorted names} share the value {value!r}.` Names are joined by `, `.
- Hint: `Review whether they mean the same concept for the same consumer. Do not collapse them unless that is intended.`
- Catalog description: `Different keys may name the same concept`.

Console output includes all locations, severity, message and hint; HTML shows
all locations and Information / Review chips. An empty rule block is
`NAME-1` followed by `No findings`.

## Error handling

**1a.** Missing or unresolved bindings select no input; they do not produce
NAME-1 findings. Shared discovery may report separate read-error skip notes.

**1b.** A selected unreadable or unrendered file contributes no leaves. The rule
continues with other selected records.

**3a.** A group with fewer than two names after credential filtering produces no
finding. Equal values alone do not justify merging keys.

## Example

Assume a binding selects `cloud-deploy.yml` with this content:

```yaml
name: cloud-deploy
parameters:
  KAFKA_URL: kafka.internal:9092
  BOOTSTRAP_SERVERS: kafka.internal:9092
  STREAMING_BROKER_ADDRESS: kafka.internal:9092
```

The rule returns one Information / Review finding, three locations and sorted
`related` names. Its message is:

```text
Keys BOOTSTRAP_SERVERS, KAFKA_URL, STREAMING_BROKER_ADDRESS share the value 'kafka.internal:9092'.
```

Two selected files containing only `KAFKA_URL` with that value produce no finding.
`POSTGRES_DBA_USER` and `POSTGRES_DBA_PASSWORD` sharing a value are removed as a
pair. Two equal application parameters are compared as, for example,
`billing.KAFKA_URL` and `billing.BOOTSTRAP_SERVERS`. An unbound copy contributes
neither names nor locations.

## Related documentation

- [Connected entities](connections.md)
- [Rule implementation](../../src/envgene_linter/rules/name1.py)
- [Rule tests](../../tests/test_name1.py)
- [Connection resolver](../../src/envgene_linter/connections.py)
- [Reporting](../../src/envgene_linter/report.py)
