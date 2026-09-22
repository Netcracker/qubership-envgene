# INT-2

## Description

INT-2 checks whether supported references from connected consumers resolve to an object in the applicable environment and source context. A definitely missing or ambiguous target produces **Warning / Fix**. A dynamic reference, unreadable target or unavailable template context produces **Information / Review**.

Credential checks establish object existence only. They do not validate the Credential type, requested property, value completeness or secret protection. Messages and keys omit reference IDs, expressions, parameter names, secret values and parser excerpts; file locations remain visible.

## Input parameters

| Input | Purpose |
| --- | --- |
| `index` | Repository root, discovered environments, local objects and safe-path boundary |
| `connections` | Existing connected entities and environment bindings; computed when omitted |
| Security bags | Connected parameter maps and selected system/deployer fields, including their Credential catalogs |
| Environment definition | ParameterSet and Resource Profile bindings under `envTemplate` |
| Selected Cloud/Namespace objects | ParameterSet lists and profile references in generated/local objects |

Credential consumers use the source selection shared with SEC-5: connected ParameterSet and Cloud/Namespace parameter maps, selected system integration and deployer fields, active registry consumers and selected Artifact Definitions with known Credential-reference fields. Unused definitions and arbitrary string keys are not reference consumers. Credential `data` is not recursively scanned for expressions.

For INT-2, an explicit ParameterSet or Resource Profile binding target also selects an existing `Namespaces/<target>/namespace.yml`, even when its bound ParameterSet or template is unavailable. Inspect its parameter sections, `credentialsId`, ParameterSet lists and profile fields. This does not widen other rules' scope.

For `profile.name`, `profile.baseline` and `profile.override_name`, first search `<environment>/Profiles`; multiple physical targets are ambiguous. With no generated target, a baseline remains unknown, while name/override use local lookup with possible unavailable template context. An unsafe or unavailable higher-priority directory blocks fallback and yields unknown; logical directory inspection does not follow external symlinks.

## Processing flow

1. Collect connected consumers while retaining their environment, source position and selected catalog. Inspect only safe repository-local documents, with cyclic YAML aliases guarded.
2. Recognize runtime `${creds.get('id')}` calls with or without a property, including calls embedded in a larger string. System/deployer fields use `envgen.creds.get('id')`. Also recognize structured `$type: credRef` with `credId`, and bare IDs in known fields such as `credentialsId`, `defaultCredentialsId` and `tokenSecret`. Unsupported/dynamic call syntax receives Review; ordinary unrelated strings do not become references.
3. Resolve system/deployer IDs against their selected catalog. For runtime references, use generated `Credentials/credentials.yml` when present; it is authoritative even when empty. An absent ID in a readable authoritative catalog is missing. An unreadable or unsafe selected catalog is unknown, without fallback. A mapping entry establishes existence without inspecting its secret contents.
4. When the generated runtime catalog is absent, a defined ID in connected shared Credentials or the selected passport companion can establish existence. Apply the passport companion first, then shared inputs in list order; the last definition of an ID determines its final entry; overlapping IDs across ordered inputs are not automatically ambiguous. An absent ID remains unknown because templates/macros can supply it during generation. Multiple physical definitions within one selected lookup bucket are ambiguous; aliases of one physical file do not create ambiguity.
5. Resolve `envSpecificParamsets`, `envSpecificE2EParamsets` and `envSpecificTechnicalParamsets` bindings for deploy, E2E and technical categories and the corresponding `deployParameterSets`, `e2eParameterSets` and `technicalConfigurationParameterSets` lists in selected Cloud/Namespace objects. ParameterSet staging lets a cluster file replace the same site filename, then adds Inventory fragments for deterministic merging; multiple fragments do not constitute ambiguity. If a binding has no local target and `envTemplate.name`, `artifact` or `templateArtifact` supplies template context, report unknown. A closed local binding without a template source is missing. Missing targets in rendered Cloud/Namespace lists remain unknown because they can come from a template.
6. Resolve `envSpecificResourceProfiles` using the first matching directory: environment `Inventory`, cluster, then `environments`; within each level use `resource_profiles`, `rp_override`, `Profiles`, then `parameters`. Several physical matches within that selected directory are ambiguous. Inspect `profile.name`, `profile.baseline` and `profile.override_name` in selected Cloud/Namespace objects, including applicable generated `Profiles` targets. An unavailable template profile or baseline remains unknown; do not assume that every profile must exist in local override directories.
7. Emit findings at the consumer reference. Deduplicate by physical location, environment, reference kind and outcome, then sort by path, line, column, environment, kind and message. Do not resolve a reference using an unrelated environment or unused definition.

## Result

| Resolution | Type / action |
| --- | --- |
| Object exists in the selected context | No finding |
| Target definitely missing | Warning / Fix |
| Ambiguous target in the selected lookup bucket | Warning / Fix |
| Dynamic, unreadable or unavailable context | Information / Review |

The catalog description is `Every reference resolves`. The console prints eighteen rule headings, with INT-2 after SEC-5 and before NAME-1. HTML contains INT-2 only when findings exist. Findings preserve CLI exit code `0`; Fix is a manual recommendation.

## Error handling

- Paths must stay inside the repository and outside `.git`, including symlink targets. Rejected selected targets are unknown rather than a reason to use a lower-priority source.
- Jinja, malformed YAML and unsupported target shapes cannot establish existence. Parser exception text is not copied into findings. An unreadable consumer cannot expose individual references and may instead have a shared discovery skip note.
- Missing remote/template context is not proof that a reference is broken. The rule fetches no external templates, renders no Jinja, runs no macros, reads no secret stores and decrypts no values.
- This is reference resolution, not complete schema validation, Credential property validation or a full generation run. Unsupported consumer shapes remain outside the reference walker.
- File paths and source positions remain available for navigation. Redaction of INT-2 messages and keys does not change other rules' output contracts.

## Example

A connected ParameterSet contains:

```yaml
name: service
parameters:
  AUTH: ${creds.get('service-auth').password}
```

If the environment's generated `Credentials/credentials.yml` contains `service-auth: {}`, INT-2 is silent: the object exists, regardless of whether it has `password`. If that catalog is `{}`, INT-2 emits a missing-target Warning / Fix at `AUTH`, using the generic key `Credential` without printing the ID or expression. If no generated catalog or connected authored definition establishes the ID, the result is unknown-target Information / Review.

## Related documentation

- [Specification](../superpowers/specs/2026-09-18-int2-design.md)
- [Connected entities](connections.md)
- [Secret protection](sec5.md)
- [Usage](../../README.md)
- [Implementation](../../src/envgene_linter/rules/int2.py)
- [Tests](../../tests/test_int2.py)
