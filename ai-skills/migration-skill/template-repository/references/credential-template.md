# Credential Template

Policy: [credential-policy.md](credential-policy.md) (read before draft).

## Path

```text
templates/env_templates/<solution>/external-credentials.yml.j2
```

## Defaults for Template-owned env-tier

```text
remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"
```

Optional confirmed static suffix (for example `/db`). Never append `credId`. Never use
`{{ current_env.namespace }}` without implementation proof.

Default create proposal: `true` (`creationOwner: envgene`) - still requires confirmation.
Override to omit `create` when pre-existing or provider.

## Script

`draft_credential_template.py` accepts only confirmed decisions (known structure + owner + create +
path). Refuses ambiguous create/path.

Do not add Passport/Shared-owned credIds to the template only for a template reference - hand off
ownership to Instance.

## Final YAML

- `create: true` only when confirmed envgene generation.
- `create: false` in plan → omit field in YAML.
- No `writeToStore` field.
- No `data`.

Shapes: [transforms.md](transforms.md).
