# Instance transforms (External Credentials)

Read when applying YAML edits. Creation owner, `create`, and `remoteRefPath` decisions come only
from confirmed records after [credential-policy.md](credential-policy.md). Do not invent values.

## Search patterns

```text
\$\{creds\.get\(['"][^'"]+['"]\)\.(username|password|secret)\}
\$\{envgen\.creds\.get\(['"][^'"]+['"]\)\.(username|password|secret)\}
\$\{cmdb\.creds\.get\(['"][^'"]+['"]\)\.(username|password|secret)\}
'#creds\{[^}]+\}'
'#credscl\{[^}]+\}'
'#credsns\{[^}]+\}'
type:\s*usernamePassword
type:\s*secret
```

## Credential file shapes (after confirmed decisions)

```yaml
<credId>:
  type: external
  secretStore: default_store
  remoteRefPath: <confirmed-path>
  # create: true  only when creationOwner=envgene and confirmed
  properties:
    - name: username
    - name: password
```

Single-value: omit `properties`. Omit `create` when plan had `false`. Never write `create: false`
or `writeToStore` into YAML. Never append `credId` to `remoteRefPath`. Always write
`secretStore: default_store` (or a confirmed store id) - EnvGene does not fill omitted values.
Never print `data` values. Remove `data` only after confirmed `writeToStore` transfer or
provisioning.

## Macro → credRef

| Before | After |
|--------|-------|
| `${creds.get('id').username}` | `$type: credRef` / `credId: id` / `property: username` |
| `${creds.get('id').password}` | `$type: credRef` / `credId: id` / `property: password` |
| `${creds.get('id').secret}` | `$type: credRef` / `credId: id` (no `property`) |

Legacy `#creds{LOGIN, PASSWORD}` → two credRef entries (username + password).

Allowed: deploy/e2e ParameterSets and passport parameter blocks.
Forbidden: `technicalConfigurationParameters`.

**Composite values (blocked):** macro inside a larger string → `NEEDS_INPUT`; split before apply.

## Generated and out-of-scope

Delete via `cleanup_generated.py` only. Never hand-edit `Credentials/` or `effective-set/`.
