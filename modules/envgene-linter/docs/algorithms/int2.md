# INT-2

- [Description](#description)
- [Input parameters](#input-parameters)
- [Processing flow](#processing-flow)
- [Result](#result)
- [Error handling](#error-handling)
- [Example](#example)
- [Related documentation](#related-documentation)

## Description

INT-2 checks whether supported references from connected consumers resolve to an object in the applicable environment and source context. A definitely missing or ambiguous target produces **Warning / Fix**. A dynamic reference, unreadable target or unavailable template context produces **Information / Review**.

Credential checks establish object existence only. They do not validate the Credential type, requested property, value completeness or secret protection. Messages and keys omit reference IDs, expressions, parameter names, secret values and parser excerpts; file locations remain visible.

## Input parameters

| Input                  | Purpose                                                                                                 |
|------------------------|---------------------------------------------------------------------------------------------------------|
| `index`                | Repository root, discovered environments, local objects and safe-path boundary                          |
| `connections`          | Existing connected entities and environment bindings; computed when omitted                             |
| Security bags          | Connected parameter maps and selected system/deployer fields, including their Credential catalogs       |
| Environment definition | ParameterSet and Resource Profile bindings under `envTemplate`, plus explicit `inventory.cloudPassport` |

Credential consumers use the authored source selection shared with SEC-5: connected ParameterSet maps and selected
system, deployer, registry, and Artifact Definition fields. Generated catalogs supply reference evidence under the
[authored configuration scope](/modules/envgene-linter/docs/algorithms/source-scope.md). Unused definitions and
arbitrary string keys are not consumers. Credential `data` is not scanned for expressions.

Modern Artifact Definition registry references use the root `configuration/credentials/credentials.yml` catalog.
For V2, only the authentication configuration selected by `registry.mavenConfig.authConfig` is active.
Literal `authMethod: anonymous` does not select a Credential. Unavailable root catalogs do not fall back to runtime
Credentials. See [INT-4 reference evidence](/modules/envgene-linter/docs/algorithms/int4.md#reference-evidence).

Explicit environment bindings remain consumers even when a local template is unavailable. Rendered Cloud and Namespace
objects do not supply additional finding targets.

Resource Profile references are checked in authored `envSpecificResourceProfiles` bindings. Generated `profile`
mappings and `Profiles/` files are outside these consumer checks. An unsafe or unavailable higher-priority authored
lookup blocks fallback and yields unknown.

## Processing flow

1. Collect connected consumers while retaining their environment, source position and selected catalog. Inspect only safe repository-local documents, with cyclic YAML aliases guarded.
2. Recognize runtime `${creds.get('id')}` calls with or without a property, including calls embedded in a larger string. System/deployer fields use `envgen.creds.get('id')`. Also recognize structured `$type: credRef` with `credId`, and bare IDs in known fields such as `credentialsId`, `defaultCredentialsId` and `tokenSecret`. Unsupported/dynamic call syntax receives Review; ordinary unrelated strings do not become references.
3. Resolve system/deployer IDs against their selected catalog. For runtime references, use generated `Credentials/credentials.yml` when present; it is authoritative even when empty. An absent ID in a readable authoritative catalog is missing. An unreadable or unsafe selected catalog is unknown, without fallback. A mapping entry establishes existence without inspecting its secret contents.
4. When the generated runtime catalog is absent, a defined ID in connected shared Credentials or the selected passport companion can establish existence. Apply the passport companion first, then shared inputs in list order; the last definition of an ID determines its final entry; overlapping IDs across ordered inputs are not automatically ambiguous. An absent ID remains unknown because templates/macros can supply it during generation. Multiple physical definitions within one selected lookup bucket are ambiguous; aliases of one physical file do not create ambiguity.
5. Resolve `envSpecificParamsets`, `envSpecificE2EParamsets`, and `envSpecificTechnicalParamsets` bindings in
   authored environment definitions. Use the shared indexed ParameterSet selection, including nested YAML and JSON.
   [Staging](/modules/envgene-linter/docs/algorithms/effective-set.md#3-staging) applies replacement by relative path
   across all three copy phases. Multiple surviving fragments do not constitute ambiguity.
   An incomplete scan, unreadable selected source, or unavailable role-specific template context is unknown.
   If a binding has no local target and `envTemplate.name`, `artifact`, or `templateArtifact` supplies template
   context, report unknown. A closed local binding without a template source is missing.
6. Resolve `envSpecificResourceProfiles` using environment `Inventory`, cluster, then `environments`.
   Within each level use `resource_profiles`, `rp_override`, `Profiles`, then `parameters`, stopping at the first
   matching directory. Several physical matches there are ambiguous.
   Generated profile mappings do not add consumers.
7. Inspect truthy `inventory.cloudPassport` references even when `envTemplate` is absent.
   Search environment `Inventory`, then cluster, then `environments`, using `cloud-passport` before `cloud-passports`
   at each level. Stop at the first matching directory. A complete missing lookup produces Fix at that field.
   Another cluster and external templates cannot supply the target. Dynamic references, incomplete higher-priority
   scans, unavailable lookup directories, unsafe or unreadable targets, unrendered `.j2` targets, and several
   distinct matches in one directory produce Review.
   The generator returns the first explicit match, so duplicate targets do not prove a generation failure.
   Absent, empty, or null explicit fields remain optional even when no automatic passport exists.
8. Emit findings at the consumer reference. Deduplicate by physical location, environment, reference kind and outcome,
   then sort by path, line, column, environment, kind, and message.
   Do not resolve a reference using an unrelated environment or unused definition.

## Result

| Resolution                                     | Type / action        |
|------------------------------------------------|----------------------|
| Object exists in the selected context          | No finding           |
| Target definitely missing                      | Warning / Fix        |
| Ambiguous target in the selected lookup bucket | Warning / Fix        |
| Dynamic, unreadable or unavailable context     | Information / Review |

The catalog description is `Every reference resolves`. INT-2 follows SEC-5 and precedes INT-3 in reports.
HTML contains INT-2 only when findings exist. Findings preserve CLI exit code `0`. Fix is a manual recommendation.
Cloud Passport findings use the generic key `Cloud Passport` and omit the explicit reference value.
Several physical candidates in one passport directory receive Review instead of the ambiguity Fix used by other reference kinds.

## Error handling

- Paths must stay inside the repository and outside `.git`, including symlink targets. Rejected selected targets are unknown rather than a reason to use a lower-priority source.
- Jinja, malformed YAML or JSON, and unsupported target shapes cannot establish existence.
  Parser exception text is not copied into findings. An unreadable consumer cannot expose individual references
  and may instead have a shared discovery skip note.
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
- [Explicit passport tests](/modules/envgene-linter/tests/test_int2_passports.py)
