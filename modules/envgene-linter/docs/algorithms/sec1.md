# SEC-1

## Description

SEC-1 reports literal values in secret-named parameters of connected objects. The standard prohibits storing a secret directly in a parameter and recommends a Credential reference instead. This first implementation uses an explicit name heuristic; it is not a general secret scanner and cannot prove whether an arbitrary value is a secret.

A parameter's last named component is normalized from camelCase to snake_case and compared case-insensitively. It must end at a token boundary with `password`, `passwd`, `pass`, `secret`, `token`, `private_key` or `api_key`. Boundaries are the start of the name, `_`, `.` or `-`. Thus `DB_PASSWORD`, `db.password` and `apiKey` match; `token.path`, `TOKEN_TTL`, `PASSWORD_LENGTH`, `credentialsId` and `secretName` do not. Trailing list indices do not change the parameter name.

## Input parameters

| Input                                                  | Source                                 | Purpose                                               |
|--------------------------------------------------------|----------------------------------------|-------------------------------------------------------|
| `index`                                                | Repository discovery                   | Discovered environments and loaded files              |
| `connections`                                          | Shared resolution; computed if omitted | Selected ParameterSets and resolved namespace targets |
| ParameterSet `parameters`, `applications[].parameters` | Selected, readable, non-Jinja files    | Inspect parameter values                              |

SEC-1 follows the [authored configuration scope](/modules/envgene-linter/docs/algorithms/source-scope.md). Generated
Cloud and Namespace objects are outside its parameter inputs.

## Processing flow

1. Compute or reuse connections. Inspect each selected authored ParameterSet once, retaining its source path.
   Skip unreadable, unsafe, and Jinja inputs.
2. Walk root and application parameter maps, including nested maps and lists. Guard recursive aliases.
3. Match each leaf's last named component against the secret-name heuristic.
4. Skip nulls, empty strings, structured `$type: credRef` nodes, and strings containing `${`, `{{`, or `{%`.
   Expressions are not evaluated, and skipping one does not prove that it resolves safely.
5. Report remaining literals, including numbers, booleans, default passwords, and literal `ENC[...]` strings.
6. Sort findings by file path, key, and line.

## Result

One Warning / Fix finding per matching leaf, at the original YAML position. The key is the complete parameter path, including section and list indices. The message describes a literal value under a secret-like name; it never includes that value. The hint recommends storing the secret in a Credential and using `${creds.get("<id>").<field>}`.

SEC-1 follows PLACE-10; SEC-3 follows SEC-1; SEC-4, SEC-5 and INT-2 follow SEC-3 before NAME-1. The console has eighteen rule headings; HTML contains only rules with findings. Findings retain CLI exit code `0`. No automatic edits, network calls, decryption or credential lookup are performed.

## Error handling

- Unavailable authored ParameterSets follow the shared source-read diagnostic contract.
   Parser exception text is omitted because it can contain source values.
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

- [Connected entities](connections.md)
- [Usage](../../README.md)
- [Implementation](../../src/envgene_linter/rules/sec1.py)
- [Tests](../../tests/test_sec1.py)
