# SEC-4

## Description

SEC-4 compares Credential IDs in references belonging to a named user/password pair. Different IDs produce **Information / Review**. Equal IDs are accepted without checking whether a Credential definition exists or contains both fields.

## Input parameters

| Input | Purpose |
| --- | --- |
| `index` | Repository boundary and discovered environments |
| `connections` | Connected-entity graph; computed when omitted |
| Security bags | Connected ParameterSet, application, Cloud/Namespace and selected system/deployer mappings |

Credential catalogs are not inspected by SEC-4. The shared security-source collector still determines the connected consumer scope.

## Processing flow

1. Collect connected consumer mappings. Keep environments, applications, nested mappings and list elements separate.
2. Normalize parameter names by splitting camelCase boundaries and ignoring letter case. Match user suffixes `USER_NAME`, `USERNAME`, `LOGIN`, `USER` and password suffixes `PASSWORD`, `PASSWD`, `PASS`, `PWD`. Prefer `USER_NAME` over a shorter interpretation. A suffix must occupy the whole name or follow a separator (`_`, `.`, or the previously supported `-`).
3. Remove the recognized suffix. Pair only sibling parameters whose remaining prefixes match exactly after normalization. Existing unprefixed `username` / `password` pairs remain supported. If several aliases share a prefix, compare each user/password combination separately.
4. Parse both values as complete supported references with literal IDs. Runtime syntax is `${creds.get("id").field}`; system/deployer syntax is `envgen.creds.get("id").field`. Structured `credRef` nodes remain supported. Skip a comparison if either value is literal, dynamic, malformed or uses syntax outside its supported context.
5. Compare the two extracted IDs exactly, including case. Do not resolve definitions or validate their types, completeness or referenced properties. A recognized `.secret` accessor does not change this ID-only comparison.
6. Emit one Information / Review finding for each pair with different IDs, including both parameter locations. Equal IDs and lone parameters produce no finding.
7. Deduplicate repeated physical findings and sort by file, line, column and message. Terminate recursive YAML aliases safely.

## Result

The finding states: `The user/password pair must reference the same Credential ID.` Messages omit IDs, reference text and secret values. The rule catalog description is `Credential pairs reference the same ID`. Findings retain CLI exit code `0`.

## Error handling

Unreadable or unsafe consumer files are skipped. Missing, ambiguous, unreadable or incomplete Credential catalogs do not produce SEC-4 findings. A comparison requires two extractable IDs; unknown expressions are skipped. No decryption, network access or file mutation occurs.

Pairs such as `USER` / `TOKEN`, `CLIENT_ID` / `CLIENT_SECRET`, `accessKey` / `accessSecret` and `principal` / `credentials` are outside the current naming scope. Definitions and secret protection are outside this rule.

## Example

Supported naming examples:

| User parameter | Password parameter |
| --- | --- |
| `DEFAULT_TENANT_ADMIN_LOGIN` | `DEFAULT_TENANT_ADMIN_PASSWORD` |
| `STORAGE_USERNAME` | `STORAGE_PASSWORD` |
| `CSE_GRAYLOG_USER` | `CSE_GRAYLOG_PASSWORD` |
| `OPENSEARCH_CLIENT_USER_NAME` | `OPENSEARCH_CLIENT_PASSWORD` |
| `DUMPS_MONGO_USER` | `DUMPS_MONGO_PASSWD` |
| `DB_USER` | `DB_PASS` |
| `db_user` | `db_pwd` |
| `kafkaAuthUsername` | `kafkaAuthPassword` |
| `sasl.username` | `sasl.password` |

```yaml
parameters:
  DEFAULT_TENANT_ADMIN_LOGIN: ${creds.get("tenant-admin").username}
  DEFAULT_TENANT_ADMIN_PASSWORD: ${creds.get("tenant-admin").password}
```

Both IDs are `tenant-admin`, so there is no finding, even if its definition is unavailable. Changing only the second ID produces a finding at the pair. A shared ID never creates a pair between unrelated parameter names.

## Related documentation

- [Specification](../superpowers/specs/2026-09-16-sec4-design.md)
- [Russian version](ru/sec4.md)
- [Connected entities](connections.md)
- [Usage](../../README.md)
- [Implementation](../../src/envgene_linter/rules/sec4.py)
- [Tests](../../tests/test_sec4.py)
