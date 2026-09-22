# PLACE-8

- [PLACE-8](#place-8)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

PLACE-8 (SHOULD) reports the empty-entity portion of the rule: connected empty
ParameterSets, Resource Profile Overrides, and credentials files receive
Information / Review. A visible binding or known generator use must select the
physical file. Review determines whether the empty slot is intentional; no file
is changed or removed. File size, application count, service names, and parameter
prefixes are not used to infer unrelated responsibilities.

## Input parameters

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `index` | Discovery → `check` | Yes | None | `RepoIndex` | Supplies environments, bindings, and discovered files |
| `connections` | Caller → `check` | No | `None`: `compute_connections(index)` | `Connections` | Selects physical files and records their uses |

## Processing flow

1. **Resolve connected physical files**

   1. Use supplied connections or calculate them from `index`. Discovery supplies
      repository `environments/`, cluster, and environment `Inventory/` records.
      Profile and credential directories are scanned recursively; generated
      `<env>/Profiles` and `<env>/Credentials` outside Inventory, `.git`, outside-repository
      paths, and Jinja templates are excluded. ParameterSet discovery retains its existing depth.
   2. Resolve ParameterSet lists in `envSpecificParamsets`, `envSpecificE2EParamsets`,
      and `envSpecificTechnicalParamsets` using shared staging. Cluster files replace
      repository files of the same staged filename; environment entries also participate.
      Keep every surviving physical path.
   3. Resolve `envSpecificResourceProfiles` (target → reference) and
      `sharedMasterCredentialFiles` (list of references) beneath `envTemplate`.
      Search Inventory, then its cluster, then repository `environments/`.
      Within each level, profiles use `resource_profiles`, `rp_override`, `Profiles`,
      `parameters`; credentials use `credentials`, `Credentials`, `shared-credentials`.
   4. Match exact `.yml`/`.yaml` stems, including indexed aliases, without normalizing
      references. Select all matches in the first occupied directory bucket and
      stop; malformed YAML still occupies a slot and shadows lower buckets.
   5. Include each discovered environment's exact
      `Inventory/credentials/inventory_generation_creds.yml` when indexed. This known
      generator input is connected without an explicit binding. Same-named cluster
      or repository files have no implicit use. Do not infer template bindings or other uses.

2. **Collect and classify candidates**

   1. Start with connected ParameterSets, add connected profiles, then connected
      credentials. Deduplicate by resolved physical path across environments and kinds;
      credential records take precedence. Require membership in `connections.selected_paths`.
   2. Treat profiles discovered in legacy `parameters/` as ParameterSet candidates initially.
      Reclassify a ParameterSet candidate as a profile when a profile binding selects it
      or any mapping in its `applications` list contains `services`.
   3. For a candidate being reclassified, skip mixed legacy payloads when any application
      mapping contains `parameters`, even an empty or null value.
   4. Skip Jinja records and records without loaded YAML. Evaluate each remaining file
      once using its resulting kind.

3. **Evaluate structural emptiness**

   1. A loaded null root, including a blank or comment-only document, is empty.
      Other non-mapping roots, including `[]`, are unknown.
   2. For ParameterSets, require root keys to be a subset of `name`, `version`,
      `description`, `parameters`, `applications`. Inspect root `parameters` first,
      then each `applications[].parameters`: any nonempty mapping is nonempty.
      A parameter key counts regardless of its value, including null, `false`, `0`,
      `""`, `{}`, or `[]`.
   3. For profiles, require root keys to be a subset of `name`, `version`, `description`,
      `baseline`, `applications`. Walk applications and services in source order.
      Any nonempty `applications[].services[].parameters` list is nonempty, even if
      its entries are incomplete. `baseline` alone contributes no payload: a connected
      baseline-only profile is empty and receives Information / Review.
   4. Missing containers contribute no payload. Present parameter containers must have
      the mapping/list type specified above; applications and services must be lists of
      mappings. Explicit null containers or wrong types produce unknown. Traversal
      stops at the first decisive unknown or nonempty state; it is not schema validation.
      When traversal finishes without either, the file is empty. Names alone add no payload.
   5. For credentials, an empty mapping is empty and any root entry is nonempty.
      Secret values are neither validated nor decrypted.

4. **Build findings**

   1. Emit a finding only for a definite empty result; unknown and nonempty results are silent.
   2. Set the location to line 1, column 1, and sort findings by
      `(path.as_posix(), key, line)`.

## Result

The returned list contains `PLACE-8` findings with severity `information`, issue
type `Information`, and action `Review`. Each uses the filename stem as `key`, one
location, no `related` locations, and scope `repository`, `<cluster>`, or `<cluster>/<env>`.

Message: `{kind} {filename!r} is empty but is referenced or used by the generator.`

`kind` is `ParameterSet`, `Resource Profile Override`, or `Credentials file`.

Hint: `Review whether this empty file is intentional. If not, populate it or remove its reference or usage.`

Catalog description: `Referenced or used entities are empty`. Console and HTML
place PLACE-8 after PLACE-7 and before PLACE-9; the empty block is `PLACE-8
No findings`.
HTML displays Information / Review chips. These findings alone retain exit code 0.
There are no new options or automatic fixes. Legacy classification does not change
other rules or add entities to NAME-2.

## Error handling

**1a.** Missing or malformed binding containers contribute no usable reference.
Unresolved and template-only references produce no candidates. Missing inventory-generation
credentials are allowed and produce no finding.

**1b.** A malformed YAML match blocks lower-priority buckets but is skipped at step 2.
Discovery read-error notes for the added entity kinds contain a path and generic
reason without YAML snippets or credential values.

**2a.** Unloaded files, Jinja, and mixed legacy profile payloads produce no finding.

**3a.** Unknown structure produces no finding. Unsupported root metadata, including
unrecognized encryption metadata, prevents ParameterSet/profile empty classification;
credential metadata itself is a root entry and makes the credentials file nonempty.

## Example

These synthetic bindings select three files whose entire content is `{}`:

```yaml
envTemplate:
  name: composite
  envSpecificParamsets:
    bss: [empty]
  envSpecificResourceProfiles:
    bss: empty-profile
  sharedMasterCredentialFiles: [empty-creds]
```

The result is three Information / Review findings, one per file. Replacing the
profile contents with `baseline: standard` keeps its Information / Review finding.
Removing the bindings makes these files unconnected and silent, unless a known
generator use independently selects them.

```bash
.venv/bin/envgene-linter check testdata/place8/not-ok
.venv/bin/envgene-linter check testdata/place8/ok
```

The [not-ok fixture](../../testdata/place8/not-ok/environments/lab-cluster/e01/Inventory/env_definition.yml)
produces three PLACE-8 findings; the [ok fixture](../../testdata/place8/ok/environments/lab-cluster/e01/Inventory/env_definition.yml)
leaves the three empty files unreferenced and produces none.

## Related documentation

- [Connected entities](connections.md)
- [Russian version](ru/place8.md)
- [PLACE-8: implementation](../../src/envgene_linter/rules/place8.py)
- [PLACE-8: tests](../../tests/test_place8.py)
- [`compute_connections`](../../src/envgene_linter/connections.py)
- [YAML positions and traversal](../../src/envgene_linter/yamlio.py)
