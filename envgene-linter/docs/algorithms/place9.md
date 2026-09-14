# PLACE-9

- [PLACE-9](#place-9)
  - [Description](#description)
  - [Input parameters](#input-parameters)
  - [Processing flow](#processing-flow)
  - [Result](#result)
  - [Error handling](#error-handling)
  - [Example](#example)
  - [Related documentation](#related-documentation)

## Description

PLACE-9 (SHOULD) checks used Cloud Passport cardinality, ambiguous resolution and passport/credential directory layout. A consuming cluster may use at most one default and at most one infra passport. Exactly the stem `passport-infra` identifies the infra role; other names identify the default role. This is not a NAME-8/9 naming check.

Only explicitly referenced or automatically used inputs participate. An ambiguity is a connected resolution attempt even though no passport can be selected for content checks. PLACE-3 continues to report passport files outside the cluster layer.

## Input parameters

| Parameter | Source | Required | Default | Values / format | Effect |
| --- | --- | --- | --- | --- | --- |
| `index` | Repository discovery | Yes | None | `RepoIndex` | Clusters, environments, passport records and bindings |
| `connections` | Engine / shared resolver | No | Computed when omitted | `Connections` | Successfully selected passports by environment |
| `inventory.cloudPassport` | Environment definition | No | Automatic resolution | Exact passport stem | Chooses the explicit resolution name |
| Passport credential slots | Files beside the selected passport | No | No finding if absent | `credentials/<stem>.yml`, then `<stem>-creds.yml` | Identifies the first existing credential input used by the local generator |

## Processing flow

1. **Collect passport resolution candidates**

   1. For an explicit reference, collect matching passport names from the environment's Inventory, its cluster, and repository `environments/`, in `cloud-passport/` and `cloud-passports/`.
   2. For automatic association, try the cluster-name passport, then `passport`, using the existing automatic search. Stop at the first nonempty name bucket; do not combine fallback names.
   3. Treat `.yml` and `.yaml` files as separate files unless they resolve to the same physical path. Exclude paths outside the repository or inside `.git`. Ignore unrelated passport names and credentials records.

2. **Report ambiguous resolution**

   1. If a used resolution attempt has more than one distinct physical candidate, create a duplicate-resolution finding.
   2. Group identical candidate sets across environments so a shared conflict is reported once.
   3. Include every candidate file at `1:1` and the affected environment-definition reference positions. For automatic association use definition position `1:1`.
   4. Do not pass ambiguous groups into successful-selection cardinality checks.

3. **Count selected passports per consuming cluster and role**

   1. Group uniquely selected physical passport files by the environment's cluster and the default/infra role.
   2. Deduplicate reuse of the same file by several environments.
   3. If a role has more than one physical file, create one finding including those passports. The default plus infra combination is allowed.

4. **Check passport directory placement**

   1. For a selected passport already owned by a cluster, require its path under that cluster's canonical `cloud-passport/` directory. Nested directories are allowed.
   2. Report a noncanonical cluster directory such as `cloud-passports/`.
   3. Leave repository/environment-layer passport placement to PLACE-3; do not repeat its finding in PLACE-9.

5. **Check the used credentials companion**

   1. For each uniquely selected passport, look first for `credentials/<passport-stem>.yml` under the passport's parent, then for `<passport-stem>-creds.yml` beside it. The first existing file occupies the input slot. If it resolves outside the repository or inside `.git`, skip this companion check without promoting the next slot.
   2. Require the used credentials file to be beside the passport and under the owning cluster's `cloud-passport/`. A selected credentials subdirectory input violates the adjacency requirement even if an unused adjacent copy also exists.
   3. Emit one finding per misplaced physical credentials file, retaining its associated passport location. Do not read or validate credential contents.

6. **Return findings**

   Return Warning / Fix findings sorted by path, key and line. Keep duplicate-resolution, role cardinality and misplaced companion findings distinct.

## Result

PLACE-9 returns warnings with concrete file locations and corrective hints; it does not rename, move or delete files. The catalog description is `One Cloud Passport per cluster`. The console always renders all thirteen catalog headers, with PLACE-9 after PLACE-8 and before PLACE-10; a silent PLACE-9 block displays `No findings`. The HTML report preserves its existing findings-only sections: it renders a PLACE-9 section only when the rule has findings and orders that section after PLACE-8 and before PLACE-10 when those sections are present. Findings preserve CLI exit code `0`.

## Error handling

**1a.** Missing references, no matching passport and unused files produce no PLACE-9 findings. Only discovered environments contribute usage.

**2a.** Ambiguity is reported from structured candidates, not by parsing resolver note text. Existing resolver skip notes may still be returned separately.

**2b.** If an environment definition cannot be read for an exact binding position, use its file position `1:1`; the known file conflict remains reportable.

**3a / 4a.** A selected passport's invalid YAML does not hide a count or placement problem: these checks need identity and location, not content.

**5a.** Missing credentials and lower-priority unused companion copies are silent. The local generator checks the listed `.yml` credential slots; this rule does not infer `.yaml` companion use or search arbitrary similarly named files.

**5b.** Files outside the repository or inside `.git` are not candidates. No external files or secret values are inspected.

## Example

Allowed: one business environment auto-selects `passport.yml`; an infra environment explicitly selects `passport-infra`:

```text
environments/c/cloud-passport/passport.yml
environments/c/cloud-passport/passport-creds.yml
environments/c/cloud-passport/passport-infra.yml
environments/c/cloud-passport/passport-infra-creds.yml
```

Two environments selecting `business-a` and `business-b` from that cluster's passport directory produce one default-role count finding. An unreferenced `backup.yml` does not affect the count.

If an explicit `cloudPassport: passport` matches both `environments/cloud-passport/passport.yml` and `environments/c/cloud-passport/passport.yml`, PLACE-9 reports the candidate conflict. It is not a merged passport.

If `credentials/passport.yml` exists under the selected passport's parent, the local generator uses it before `passport-creds.yml`; PLACE-9 reports that used subdirectory companion as misplaced.

## Related documentation

- [Russian version](ru/place9.md)
- [Connected entities](connections.md)
- [Passport layer placement: PLACE-3](place3.md)
- [Implementation](../../src/envgene_linter/rules/place9.py)
- [Passport resolver](../../src/envgene_linter/passport.py)
- [Tests](../../tests/test_place9.py)
- [Design](../superpowers/specs/2026-09-11-place9-design.md)
