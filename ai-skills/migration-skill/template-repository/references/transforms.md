# Template transforms (External Credentials)

Use only **confirmed** create/path decisions from [credential-policy.md](credential-policy.md).
Do not invent values while editing YAML.

## Search patterns

```text
\$\{creds\.get\(['"][^'"]+['"]\)\.(username|password|secret)\}
\$\{envgen\.creds\.get\(['"][^'"]+['"]\)\.(username|password|secret)\}
\$\{cmdb\.creds\.get\(['"][^'"]+['"]\)\.(username|password|secret)\}
'#creds\{[^}]+\}'
'#credscl\{[^}]+\}'
'#credsns\{[^}]+\}'
```

## Credential Template entry (confirmed)

```yaml
<credId>:
  type: external
  secretStore: default_store
  remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"
  # create: true only when confirmed
  properties:
    - name: username
    - name: password
```

Single-value: omit `properties`. Omit `create` when plan was false. Never write `create: false`.
Never append `credId` to `remoteRefPath`.

## Macro → credRef

Use `scripts/replace_macros.py`. Allowed in deploy/e2e ParameterSets only. Forbidden in
`technicalConfigurationParameters`. Built-in fields stay plain `credId` strings.
