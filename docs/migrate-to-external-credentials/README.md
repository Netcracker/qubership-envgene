# Migrate to External Credentials

One place for EnvGene cutover from local Credentials to External Credentials: how-tos, agent
skills, and a pointer to the migration CLI.

- [Layers](#layers)
- [Layout](#layout)
- [Order](#order)
- [Out of scope](#out-of-scope)

## Layers

| Layer | Location | Does | Does not |
|-------|----------|------|----------|
| How-to | [how-to/](how-to/) | Human procedure | Edit YAML for you |
| Skills | [skills/](skills/) | YAML cutover via scripts + confirmations | Pipeline, Store writes, passwords/tokens |
| CLI | [cli/](cli/) | `collect` / `export-credentials` / `fill` for Store transfer | Edit Instance Credential YAML |

Specification: [External Credentials Management](/docs/features/external-creds.md).

Store write after fill: [External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md).

## Layout

```text
docs/migrate-to-external-credentials/
  README.md
  how-to/
    overview.md
    migrate-template-repository.md
    migrate-instance-repository.md
    transfer-secrets-to-store.md
  skills/
    shared/                 # report format + extcreds_mig Python helpers
    template-repository/    # SKILL.md + scripts
    instance-repository/    # SKILL.md + scripts

cli/                        # pip package — collect / export-credentials / fill
```

## Order

1. Template Repository YAML cutover (`migrate-template-repository`) → publish a concrete Template
   version.
2. If actual passwords and tokens are still in the Instance Repository: `migration-cli collect`
   **before** Instance cutover.
3. Instance Repository YAML cutover (`migrate-instance-repository`).
4. Effective Set with `EXTERNAL_CREDENTIAL_PROVISIONING=skip` (Context only).
5. Transfer secrets: `export-credentials` (Jenkins path) if needed → `fill` →
   `external-cred-provision`.
6. Effective Set with `EXTERNAL_CREDENTIAL_PROVISIONING=apply` (default), then test deploy and
   remaining environments.

See [overview Flow](how-to/overview.md#flow). Skills and how-tos stop at handoff. They do not run
the pipeline.

## Out of scope

- Pipeline orchestration inside skills
- Blue-Green and template composition
- Template Repository system credentials (local-only by design)
- Putting actual passwords or tokens in Git, MRs, or migration notes
