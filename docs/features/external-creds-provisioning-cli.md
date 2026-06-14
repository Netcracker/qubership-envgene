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
| `--dry-run`                | off     | Run checks only, no writes                           |

When `--dry-run` is set, the CLI runs the [Dry-run phase](#dry-run-phase). No writes happen.

## Environment variables

All store configuration is read from the process environment. The CLI determines the
store type from the VALS reference scheme in each credential's `vals` field
(`ref+vault://...` → `vault`, `ref+gcpsecrets://...` → `gcp`, `ref+awssecrets://...` →
`aws`).

For each store type, the CLI reads the following variables from the process
environment. When the `vals` reference carries a `secret_store_id` query parameter,
the CLI prepends the value as-is to each bare name, with `_` as separator (not part of
the value). The value is expected to match `[A-Za-z0-9_]+`.

The right column illustrates with `secret_store_id=secret_store`:

| Store type | Without `secret_store_id`                    | With `secret_store_id=secret_store`                                    |
|------------|----------------------------------------------|------------------------------------------------------------------------|
| `vault`    | `VAULT_TOKEN`                                | `secret_store_VAULT_TOKEN`                                             |
| `gcp`      | `GOOGLE_APPLICATION_CREDENTIALS`             | `secret_store_GOOGLE_APPLICATION_CREDENTIALS`                          |
| `aws`      | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | `secret_store_AWS_ACCESS_KEY_ID`, `secret_store_AWS_SECRET_ACCESS_KEY` |

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
    # or defaults to `default_store` when the parameter is absent.
    vals: string
    # Mandatory
    # See the Strategy enum section for the meaning of each value.
    strategy: enum [fail_if_absent, create_if_absent, overwrite]
    # Mandatory
    # Credential content. Two shapes are accepted:
    #
    # - Map of named field values for a multi-field credential (for example
    #   `username` and `password` for the usernamePassword pair), or for a
    #   single-value credential in a store that requires a named field
    #   (for example Vault, where the secret path must carry a field segment).
    #
    # - Scalar string for a single-value credential in a store that addresses
    #   the secret directly (for example GCP Secret Manager).
    #
    # Each value (the scalar, or each field value in the map) is either a real
    # plaintext value or the reserved marker `_generateValue`.
    data: string | map
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
      password: _generateValue

  mq-connection-secret:
    vals: "ref+vault://kv/data/env-1/mq-connection-secret"
    strategy: create_if_absent
    data:
      value: token

  third-party-api-token:
    vals: "ref+gcpsecrets://example-project/third-party-api-token"
    strategy: fail_if_absent
    data: _generateValue
```

> [!IMPORTANT]
> `_generateValue` is a reserved marker in the EnvGene catalogue of reserved values.
> It signals "CLI must generate this" during provisioning.

## Strategy enum

The strategy is an attribute on each credential entry in the context.

| Strategy           | Credential is present    | Credential is absent  |
|--------------------|--------------------------|-----------------------|
| `fail_if_absent`   | skip the credential      | fail                  |
| `create_if_absent` | skip the credential      | create the credential |
| `overwrite`        | overwrite the credential | create the credential |

The "credential is present" check is performed via the store's `list` operation against
the target path. The CLI does not `get` the credential value and does not validate the
structure or the content of an existing credential.

A per-credential failure does not stop the run. The CLI logs each
failure and continues with the next credential so the log carries the full list of
failures. The summary line tallies them.

In dry-run mode the CLI performs no writes. For each strategy, the CLI runs the
prerequisite check shown below.

| Strategy           | Dry-run check                                              |
|--------------------|------------------------------------------------------------|
| `fail_if_absent`   | the credential exists at the target path                   |
| `create_if_absent` | the authenticated principal can create at the target path  |
| `overwrite`        | the authenticated principal can create at the target path  |

## Value generation

When the CLI writes a credential and `data` carries the `_generateValue` marker —
either as the scalar value, or as a value inside the `data` map — the CLI generates a
value following the rules below. The rules apply to every occurrence of the marker.

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

1. **Check env vars.** For every distinct store referenced by `vals` fields, the
   corresponding environment variables are present in the process environment.
2. **Check authentication.** Authenticate to each referenced store using its
   environment variables.

On failure, the CLI logs the failure and exits non-zero. No further phase runs.

### Processing phase

Runs in apply mode (non `--dry-run`). For each `credentials.<id>` entry, in input order
apply the strategy per the behaviour table in [Strategy enum](#strategy-enum). When
the strategy calls for a write, generate values for each `_generateValue`
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
