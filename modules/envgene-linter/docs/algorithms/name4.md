# NAME-4

- [NAME-4](#name-4)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

NAME-4 checks that each bound ParameterSet stem is `<subject>-<category>` and
contains no cluster/environment identifier from its actual users, ticket or
release marker. All findings are Information / Review. It reads selected stems
and bindings without merging an Effective Set or changing files.

## Input parameters

These are inputs to `check(index, connections=None)`, not additional CLI options.

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `index` | Rule argument from repository discovery | Yes | None | `RepoIndex` with ParameterSets and environment bindings | Supplies data for shared connection resolution |
| `connections` | Optional rule argument / shared resolver | No | `compute_connections(index)` | `Connections.parameter_files` and `parameter_uses` | Supplies selected stems, bound categories and actual cluster/environment users |

## Processing flow

1. **Select files and their actual uses**

   1. Reuse `connections`, or compute it from `index` when omitted.
   2. Iterate `connections.parameter_uses` by physical path and look up the
      corresponding record in `parameter_files`. Skip entries without a record.
   3. Use that selected record's stem and path. Deduplicate physical aliases;
      an unrelated same-stem file or unused alias does not contribute.
   4. Collect categories from this file's uses and cluster/environment names
      by splitting each use's `environment` identifier at the first `/`.

2. **Determine required category tokens**

   1. Map deploy (`envSpecificParamsets`) to `deploy`, end-to-end
      (`envSpecificE2EParamsets`) to `pipeline`, and technical
      (`envSpecificTechnicalParamsets`) to `technical`.
   2. Form `scope` from the sorted distinct required tokens joined by a comma followed by a space.
      A file selected in multiple categories must satisfy all of them.

3. **Reject embedded scope, ticket or release markers**

   1. Search for ticket regular expression `(?:^|-)(?:ticket|jira|issue)-\d+`
      case-insensitively, and release regular expression
      `(?:^|-)(?:r\d+(?:-\d+)?|20\d{2}[.-]\d{1,2})` case-sensitively.
      These are searches, with no required boundary after the matched marker.
   2. Compare each non-empty actual cluster/environment name case-insensitively
      against the whole stem or a hyphen-bounded prefix, infix or suffix.
      Words such as `env`, `cluster` and `site` are not otherwise forbidden.
   3. If any check matches, emit the scope/ticket message and continue to the next
      file. This branch takes priority over the category-tail check.

4. **Validate subject and category tail**

   1. Split the stem on `-`. Require at least two tokens and every token before
      the last to be non-empty.
   2. Require the set of required category tokens to equal the singleton set
      containing the last token, using exact case. Nothing may follow that tail.
      Multiple distinct categories therefore cannot be satisfied by one stem.
   3. On failure, emit the tail message with sorted required tokens joined by `/`.
      Otherwise emit nothing. This step imposes no separate kebab-case check.

5. **Return ordered findings**

   1. Emit at most one finding per selected physical file, using the selected
      record's path at `1:1`, the stem as `key`, one location and empty `related`.
   2. Sort by path, key and line.

## Result

The result is a list of `NAME-4` findings with `severity=information`,
`issue_type=Information` and `action=Review`.

- Scope/ticket message: `ParameterSet {stem!r} bakes a cluster, environment, ticket or release into the name.`
- Tail message: `ParameterSet {stem!r} must end with -{token} to match its env_definition binding ({scope}).`
- Hint for either branch: `Review whether this stem can be <subject>-<category>. Do not rename it if env_definition or other logic still depends on the current spelling.`
- Catalog description: `Bound ParameterSet stem is <subject>-<category>`.

Console output includes the location, severity, message and hint; HTML shows the
location and Information / Review chips. An empty block is `NAME-4` followed by
`No findings`.

## Error handling

**1a.** Unresolved bindings and unrendered Jinja do not enter shared ParameterSet
selection. They do not create category or owner requirements for another file.

**1b.** A missing selected record is skipped. A selected record with a YAML load
error can still have its stem checked: NAME-4 does not inspect its content.

**4a.** Missing subjects (`deploy`, `-deploy`, `a--deploy`), a wrong tail, or
conflicting category requirements produce the tail finding. No automatic rename
or `env_definition` update is performed.

## Example

Assume these files are selected by bindings and none of their subjects matches
an actual cluster/environment name:

| Selected stem                    | Binding category      | NAME-4 result                                                       |
|----------------------------------|-----------------------|---------------------------------------------------------------------|
| `bss`                            | deploy                | One tail finding; `scope=deploy`                                    |
| `bss-deploy`                     | deploy                | No finding                                                          |
| `postgresql-pipeline`            | end-to-end            | No finding                                                          |
| `-deploy`                        | deploy                | One tail finding: empty subject                                     |
| `postgresql-deploy-ha`           | deploy                | One tail finding: last token is `ha`                                |
| `bss-deploy` (one physical file) | deploy and end-to-end | One tail finding; token `deploy/pipeline`, scope `deploy, pipeline` |
| `jira-123-bss-deploy`            | deploy                | One scope/ticket finding                                            |

For `bss`, the exact message is:

```text
ParameterSet 'bss' must end with -deploy to match its env_definition binding (deploy).
```

An unbound `extra.yml` is silent. Two distinct physical `bss-deploy.yml` files
keep separate categories and owners; an end-to-end use of one cannot affect the other.

## Related documentation

- [Connected entities](connections.md)
- [Rule implementation](../../src/envgene_linter/rules/name4.py)
- [Rule tests](../../tests/test_name4.py)
- [Connection resolver](../../src/envgene_linter/connections.py)
- [Reporting](../../src/envgene_linter/report.py)
