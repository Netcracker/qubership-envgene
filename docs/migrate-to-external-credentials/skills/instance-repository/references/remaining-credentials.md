# Remaining Credentials (parameters and generated)

Policy for create/path on Credential sources: [credential-policy.md](credential-policy.md).

## Parameter macros

Replace only in `deployParameters`, `e2eParameters`, and ParameterSets that feed them.
Never put `credRef` in `technicalConfigurationParameters`.
Use `scripts/replace_macros.py`.

**Composite values (blocked):** macro embedded in a larger string cannot become `$type: credRef`.
Exit `NEEDS_INPUT`; split into separate parameters before apply.

Template-dependent Credentials: use Template handoff create/path. Do not recalculate without new
evidence. Conflict → `NEEDS_INPUT`.

## Generated and out-of-scope cleanup

Delete via `cleanup_generated.py`:

- `environments/<cluster>/<env>/Credentials/credentials.yml|yaml` (generated)
- `environments/<cluster>/app-deployer/deployer-creds.yml` (No-CMDB - out of scope)
- orphaned Shared Credential files (no consumer references)

Do not remove source Passport / Shared / System files that are in use.

Shapes: [transforms.md](transforms.md).
