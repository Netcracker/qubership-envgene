# Credential Template

Policy: [credential-policy.md](credential-policy.md) (read before draft).

## Path

One file per Template Descriptor. Filename stem matches the descriptor stem (`bss.yaml` →
`bss.yml.j2`):

```text
templates/external-credentials/<descriptor-stem>.yml.j2
```

## Defaults for Template-owned env-tier

```text
remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"
```

Optional confirmed static suffix (for example `/db`). Never append `credId`. EnvGene does **not**
support `{{ current_env.namespace }}` in the Credential Template Jinja context - do not use it, even
as a manual override. Per-namespace Store paths belong in Instance migration or a confirmed static
suffix.

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
- Always set `secretStore: default_store` (or another id from the consuming Instance
  `secret-stores.yml`). EnvGene does not fill schema defaults and does not fall back when the
  field is omitted.
- No `data`.

Shapes: [transforms.md](transforms.md).
