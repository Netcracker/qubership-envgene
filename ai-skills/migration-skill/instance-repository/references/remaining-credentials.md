# Remaining Credentials (parameters and generated)

Policy for create/path on Credential sources: [credential-policy.md](credential-policy.md).

## Parameter macros

Replace only in `deployParameters`, `e2eParameters`, and ParameterSets that feed them.
Never put `credRef` in `technicalConfigurationParameters`.
Use `scripts/replace_macros.py`.

Template-dependent Credentials: use Template handoff create/path. Do not recalculate without new
evidence. Conflict → `NEEDS_INPUT`.

## Generated cleanup

Delete only `environments/<cluster>/<env>/Credentials/credentials.yml|yaml` via
`cleanup_generated.py`. Do not remove source Passport / Shared / System files.

Shapes: [transforms.md](transforms.md).
