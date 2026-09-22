# PLACE-3

- [PLACE-3](#place-3)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

PLACE-3 checks the placement of selected Cloud Passport files. A passport belongs at the cluster layer. The current implementation checks file placement only; Cloud Passport keys inside ParameterSets are handled by PLACE-4.

## Input parameters

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `index` | Repository discovery | Yes | None | `RepoIndex` with passport records | Supplies physical paths and owning layer |
| `connections` | Shared connection resolver | No | Computed when omitted | `Connections.passports` | Selects explicitly referenced or automatically chosen passports |
| `full`, `lower`, `site`, `catalogs` | Engine | Yes in current call signature | None | Effective Set maps / passport catalogs | Compatibility inputs; not inspected by this rule |

## Processing flow

1. **Select used passports**

   Use the shared connection index supplied by the engine, or compute it for a direct call. Selection uses `inventory.cloudPassport` or the existing automatic cluster-passport resolution.

2. **Check each indexed passport's layer**

   1. Compare its resolved physical path with the selected passport set; skip unselected files.
   2. A passport with a cluster owner and no environment owner is at the cluster layer: skip it.
   3. For each remaining selected passport, create a finding at file position `1:1`. Placement does not require readable YAML content.

3. **Choose the suggested destination**

   1. If the passport has a cluster owner, recommend `environments/<cluster>/cloud-passport/`.
   2. Otherwise, if the index contains exactly one cluster, recommend that cluster's directory.
   3. Otherwise, recommend a cluster's `cloud-passport/` without choosing a cluster.

4. **Return placement findings**

   Use the passport stem as key and its cluster, or `repository`, as scope. Return findings in indexed passport order.

## Result

Each selected passport outside the cluster layer produces Warning / Fix with message `Passport <stem> is not at the cluster layer.` The hint names the destination selected in step 3. No key-by-key findings, merging, or file moves are performed. An empty result is displayed as `No findings`; findings preserve CLI exit code `0`.

## Error handling

**1a.** A missing or ambiguous passport reference may leave no selected passport; resolver notes are separate. PLACE-3 does not invent a missing-file finding.

**2a.** Unselected passports are ignored even when misplaced.

**2b.** Unreadable or Jinja passport content does not suppress a placement finding if that file was selected: its location is still known. This does not imply rendering or content validation.

## Example

An environment references `inventory.cloudPassport: cp`. The selected file is:

```text
environments/c/e/Inventory/cloud-passport/cp.yml
```

PLACE-3 produces one Warning / Fix at `cp.yml:1:1` and recommends `environments/c/cloud-passport/`.

A selected `environments/c/cloud-passport/cp.yml` is correctly placed and produces no finding. An unused passport under an environment also produces no finding because it is outside the selection.

## Related documentation

- [Russian version](ru/place3.md)
- [Connections](connections.md)
- [Effective Set](effective-set.md)
- [Implementation](../../src/envgene_linter/rules/place3.py)
- [Tests](../../tests/test_place3.py)
- [Passport keys in ParameterSets](place4.md)
