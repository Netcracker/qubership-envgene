# Template Descriptor

Read before registering `external_credential_template`.

## Rule

Credential Template file must already exist. Then set (stem matches descriptor):

```yaml
external_credential_template: "{{ templates_dir }}/external-credentials/<descriptor-stem>.yml.j2"
```

Use `scripts/register_descriptor.py` (fails if the `.j2` file is missing).

Path must use `{{ templates_dir }}` consistently with sibling fields.

Once set, every referenced `credId` must be declared in the Credential Template (or come from
Passport/Shared at Instance time). Generation fails otherwise.

## Done check

- Descriptor has `external_credential_template`
- Path points at the real `.j2` file
- Credential Template stem matches descriptor stem
