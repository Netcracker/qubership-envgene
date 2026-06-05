# External Credentials provisioning CLI

- [External Credentials provisioning CLI](#external-credentials-provisioning-cli)
  - [Synopsis](#synopsis)
  - [Arguments](#arguments)
    - [Positional](#positional)
    - [Options](#options)
  - [Environment variables](#environment-variables)
  - [Input format](#input-format)
  - [Strategy enum](#strategy-enum)
  - [Value generation](#value-generation)
  - [Behaviour](#behaviour)
    - [Pre-flight phase](#pre-flight-phase)
    - [Processing phase](#processing-phase)
    - [Dry-run phase](#dry-run-phase)
    - [Post-processing](#post-processing)

## Synopsis

```bash
external-cred-provision [OPTIONS] <context-path>
```

```bash
external-cred-provision effective-set/external-credential/external-credentials.yaml
```

Dry-run against the same context.

```bash
external-cred-provision --dry-run effective-set/external-credential/external-credentials.yaml
```

## Arguments

### Positional

- **`<context-path>`** (required). Path to the external credentials context YAML. The
  schema is defined in [Input format](#input-format).

### Options

| Flag                       | Default | Meaning                                              |
|----------------------------|---------|------------------------------------------------------|
| `--dry-run`                | off     | Run prerequisite checks only, no writes              |

When `--dry-run` is set, the CLI runs the [Dry-run phase](#dry-run-phase). No writes happen.

## Environment variables

All store configuration is read from the process environment. The CLI determines the
store type from the VALS reference scheme in each credential's `vals` field
(`ref+vault://...` → `vault`, `ref+gcpsecrets://...` → `gcp`, `ref+awssecrets://...` →
`aws`). The store identifier comes from the `secret_store_id` query parameter in
`vals`, or defaults to `default-store` when the parameter is absent.

For each store identifier, the CLI looks up variables prefixed with the store name.

| Store type | Variable(s)                                                                |
|------------|----------------------------------------------------------------------------|
| `vault`    | `<SECRET_STORE>_VAULT_TOKEN`                                               |
| `gcp`      | `<SECRET_STORE>_GOOGLE_APPLICATION_CREDENTIALS`                            |
| `aws`      | `<SECRET_STORE>_AWS_ACCESS_KEY_ID`, `<SECRET_STORE>_AWS_SECRET_ACCESS_KEY` |

The variable suffix conventions (`VAULT_TOKEN`, `GOOGLE_APPLICATION_CREDENTIALS`, etc.)
follow the `secret_manager` module contract per store type. The authoritative source is
the module documentation.

One variable set per store covers both read (existence check) and write (create or
overwrite).

## Input format

The CLI reads the external credentials context YAML at the path given as the positional
argument.

The context is a `credentials` map. Each entry addresses a secret with a VALS reference
string, a strategy enum value, and a `data` map that describes the credential content.
The CLI infers the store type from the VALS scheme and adapts `data` to the target
store's format. Store configuration and authentication come from the process environment
(see [Environment variables](#environment-variables)).

```yaml
# Mandatory
credentials:
  # Map key is the Credential id.
  <cred-id>:
    # Mandatory
    # VALS reference string that addresses the secret. The string is a path only — no
    # key segments (no `#` fragment). The CLI infers the store type from the VALS
    # scheme. The store identifier comes from the `secret_store_id` query parameter,
    # or defaults to `default-store` when the parameter is absent.
    vals: string
    # Mandatory
    # See the Strategy enum section for the meaning of each value.
    strategy: enum [fail_if_absent, create_if_absent, create_if_present]
    # Mandatory
    # Credential content as a map of named field values. The shape reflects the
    # credential's structure: `value` for a single-value
    # credential (token, secret); `username` and `password` for the usernamePassword
    # pair. Each value is either a real
    # plaintext value or the reserved marker `envgeneGenerateValue`.
    data:
      username: string
      password: string
      value: string
```

Example:

```yaml
credentials:
  db-app-cred:
    vals: "ref+vault://kv/data/env-1/db-app-cred"
    strategy: create_if_absent
    data:
      username: username
      password: password

  db-readonly-cred:
    vals: "ref+vault://kv/data/env-1/db-readonly-cred"
    strategy: fail_if_absent
    data:
      username: username
      password: envgeneGenerateValue

  mq-connection-secret:
    vals: "ref+vault://kv/data/env-1/mq-connection-secret"
    strategy: create_if_absent
    data:
      value: token

  third-party-api-token:
    vals: "ref+gcpsecrets://example-project/third-party-api-token"
    strategy: fail_if_absent
    data:
      value: envgeneGenerateValue
```

> [!IMPORTANT]
> `envgeneGenerateValue` is a reserved marker in the EnvGene catalogue of reserved values.
> It signals "CLI must generate this" during provisioning.

## Strategy enum

The strategy is an attribute on each credential entry in the context.

| Strategy             | Credential is present    | Credential is absent  |
|----------------------|--------------------------|-----------------------|
| `fail_if_absent`     | skip the credential      | fail                  |
| `create_if_absent`   | skip the credential      | create the credential |
| `create_if_present`  | overwrite the credential | create the credential |

A per-credential failure does not stop the run. The CLI logs each
failure and continues with the next credential so the log carries the full list of
failures. The summary line tallies them.

In dry-run mode the CLI performs no writes. For each strategy, the CLI runs the
prerequisite check shown below.

| Strategy             | Dry-run check                                              |
|----------------------|------------------------------------------------------------|
| `fail_if_absent`     | the credential exists at the target path                   |
| `create_if_absent`   | the authenticated principal can create at the target path  |
| `create_if_present`  | the authenticated principal can create at the target path  |

## Value generation

When the CLI writes a credential and a `data` field carries the `envgeneGenerateValue`
marker, the CLI generates a value following the rules below. The rules apply to both
multiple-value and single-value credential types.

Generated values use **only** characters from this set:

- Letters: `a-z`, `A-Z`
- Digits: `0-9`
- Basic symbols: `-` `_` `.` `:` `/`
- Grouping: `(` `)` `[` `]` `{` `}`
- Angle brackets: `<` `>`
- Common symbols: `@` `#` `%` `+` `=` `,` `;` `~` `&` `*` `|` `^` `` ` `` `?` `!`

Length is 16 characters.

## Behaviour

### Pre-flight phase

Runs before any per-credential work.

1. **Check env vars.** For every unique store identifier referenced by `vals` fields
   (the `secret_store_id` query parameter, or `default-store` when absent), the
   corresponding prefixed environment variables are present.
2. **Check authentication.** Authenticate to each referenced store using the prefixed
   environment variables.

On failure, the CLI logs the failure and exits non-zero. No further phase runs.

### Processing phase

Runs in apply mode (non `--dry-run`). For each `credentials.<id>` entry, in input order
apply the strategy per the behaviour table in [Strategy enum](#strategy-enum). When
the strategy calls for a write, generate values for each `envgeneGenerateValue`
marker using the default pattern for the field. Real values from `data` go through
as is. Write the result to the store through `secret_manager`. Log the outcome.

A single credential failure does not stop the run. The CLI keeps processing the
remaining credentials.

### Dry-run phase

Runs in `--dry-run` mode in place of the Processing phase. For each `credentials.<id>`
entry, in input order run the per-strategy prerequisite check from the dry-run table
in [Strategy enum](#strategy-enum). No writes happen. Log the outcome.

A check failure does not stop the run.

### Post-processing

Emits a summary line and sets the exit code.

- **Apply mode:** counts of `created`, `overwritten`, `skipped`, `verified`, and
  `failed`.
- **Dry-run mode:** counts of `dry_run_ok` and `dry_run_fail`.

The exit code is non-zero if any credential failed or if any earlier phase failed.
