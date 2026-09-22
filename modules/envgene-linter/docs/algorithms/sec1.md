# SEC-1

## Description

SEC-1 reports literal values in secret-named parameters of connected objects. The standard prohibits storing a secret directly in a parameter and recommends a Credential reference instead. This first implementation uses an explicit name heuristic; it is not a general secret scanner and cannot prove whether an arbitrary value is a secret.

A parameter's last named component is normalized from camelCase to snake_case and compared case-insensitively. It must end at a token boundary with `password`, `passwd`, `pass`, `secret`, `token`, `private_key` or `api_key`. Boundaries are the start of the name, `_`, `.` or `-`. Thus `DB_PASSWORD`, `db.password` and `apiKey` match; `token.path`, `TOKEN_TTL`, `PASSWORD_LENGTH`, `credentialsId` and `secretName` do not. Trailing list indices do not change the parameter name.

## Input parameters

| Input | Source | Purpose |
| --- | --- | --- |
| `index` | Repository discovery | Discovered environments and loaded files |
| `connections` | Shared resolution; computed if omitted | Selected ParameterSets and resolved namespace targets |
| ParameterSet `parameters`, `applications[].parameters` | Selected, readable, non-Jinja files | Inspect parameter values |
| `deployParameters`, `e2eParameters`, `technicalConfigurationParameters` | Known used Cloud/Namespace files | Inspect the same parameter categories on generated objects |

Cloud input is the fixed `cloud.yml` of a discovered environment. Namespace input is `Namespaces/<target>/namespace.yml` only when a local ParameterSet or resource-profile binding actually resolves for that target. A missing reference does not establish namespace use. Namespace objects known only through unavailable template/runtime inputs are outside this implementation.

## Processing flow

1. Compute or reuse the shared connections. Read each selected physical ParameterSet once, retaining its selected source path. Skip unreadable and Jinja ParameterSets.
2. Inspect the top-level and application parameter maps. Recursively visit nested maps and lists; guard against recursive YAML aliases.
3. Inspect the fixed Cloud paths and the Namespace paths selected by resolved bindings. Exclude absent files, paths outside the repository and paths inside `.git`. Deduplicate physical object paths.
4. Match each leaf's last named component against the secret-name heuristic. Ignore leaves whose names do not match.
5. Skip null and empty strings. Skip structured `$type: credRef` nodes and strings containing `${`, `{{` or `{%`: expressions are not evaluated. This skip is not a guarantee that the expression resolves to a safe value.
6. Report remaining literals, including numeric and boolean values, simple/default passwords and literal `ENC[...]` strings. SEC-1 checks direct parameter storage; it does not validate encryption or grant exceptions for strings that merely resemble placeholders.
7. Return findings sorted by file path, key and line.

## Result

One Warning / Fix finding per matching leaf, at the original YAML position. The key is the complete parameter path, including section and list indices. The message describes a literal value under a secret-like name; it never includes that value. The hint recommends storing the secret in a Credential and using `${creds.get("<id>").<field>}`.

SEC-1 follows PLACE-10; SEC-3 follows SEC-1; SEC-4, SEC-5 and INT-2 follow SEC-3 before NAME-1. The console has eighteen rule headings; HTML contains only rules with findings. Findings retain CLI exit code `0`. No automatic edits, network calls, decryption or credential lookup are performed.

## Error handling

- Malformed or non-map Cloud/Namespace documents are skipped. Parser exception text is not emitted by SEC-1 because it may contain source values.
- Unused files, credentials documents and missing references produce no SEC-1 findings. The rule does not search arbitrary repository YAML.
- A secret with an unrecognized parameter name can be missed; an ordinary value under a secret-like name can be reported. Review the finding in context.
- The rule does not validate reference syntax, existence, or the final value of macros, and does not implement SEC-2 or SEC-3.
- SEC-1 findings omit values. Other existing rules and discovery diagnostics have their own output behavior; this change does not promise global report redaction.

## Example

The values below are synthetic:

```yaml
parameters:
  DB_PASSWORD: example-password  # SEC-1
  API_KEY: ${creds.get("api-cred").secret}  # no SEC-1
  LOG_LEVEL: info  # no SEC-1
  db:
    instances:
      - password: example-password  # SEC-1
```

`DB_PASSWORD: ""` gives no finding. `DB_PASSWORD: changeme` does: the rule does not assume a simple password is unused or harmless. A Credential object's `data.password` is outside the parameter bags checked by SEC-1.

## Related documentation

- [Specification](../superpowers/specs/2026-09-16-sec1-design.md)

- [Russian version](ru/sec1.md)
- [Connected entities](connections.md)
- [Usage](../../README.md)
- [Implementation](../../src/envgene_linter/rules/sec1.py)
- [Tests](../../tests/test_sec1.py)
