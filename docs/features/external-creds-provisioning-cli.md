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
    - [Dry-run phase](#dry-run-phase)
    - [Processing phase](#processing-phase)
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

The `--dry-run` flag stops execution after the [Dry-run phase](#dry-run-phase).
Processing and Post-processing phases do not run.

## Environment variables

Store authentication variables are read from the process environment. For each Secret
Store entry in `secretStores`, the CLI looks up variables prefixed with the store name in
upper-snake form (hyphens replaced with underscores, all uppercase). Store `default-store`
maps to the prefix `DEFAULT_STORE_`. Store `gcp-primary` maps to `GCP_PRIMARY_`.

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

The context carries two sections. The `secretStores` map provides store endpoint and
authentication lookup. The `credentials` map addresses each secret in the store with a
VALS reference string, a strategy enum value, and a `data` field map.

```yaml
# Mandatory
# Map of Secret Store definitions referenced by the credentials in the context.
secretStores:
  # Map key is the Secret Store name. Referenced from credential entries through the
  # `secret_store_id` query parameter in `vals`, or used as the `default-store` fallback
  # when the parameter is absent.
  <secret-store-name>:
    # Mandatory
    type: enum [ vault, azure, aws, gcp ]
    # Mandatory
    url: url
    # Mandatory when `type` is `vault`
    # KV mount path inside Vault.
    mountPath: string
    # Mandatory when `type` is `azure`
    # Azure Key Vault name.
    vaultName: string
    # Mandatory when `type` is `aws`
    # AWS region of the Secrets Manager instance.
    region: string
    # Mandatory when `type` is `gcp`
    # GCP project that owns the secret.
    projectId: string

# Mandatory
credentials:
  # Map key is the Credential id.
  <cred-id>:
    # Mandatory
    # VALS reference string that addresses the secret as a whole. The string carries no
    # key segment after `#`. The store is selected by the `secret_store_id` query
    # parameter when present. When absent, the entry named `default-store` in 
    # `secretStores` is used.
    vals: string
    # Mandatory
    # See the Strategy enum section for the meaning of each value.
    strategy: enum [fail_if_absent, create_if_absent, create_if_present]
    # Mandatory
    # Map of plaintext field values. Keys depend on the source Credential type. For
    # multiple-value, the keys are `username` and `password`. For single-value cases
    # the key is `secret`. Each value is either a real
    # plaintext value or the reserved marker `envgeneGenerateValue`. A real value goes
    # to the store as is. The marker tells the CLI to generate a value using the
    # default pattern for the field.
    data:
      username: string
      password: string
      secret: string
```

Example:

```yaml
secretStores:
  default-store:
    type: vault
    url: "https://vault.example.com"
    mountPath: kv
  gcp-primary:
    type: gcp
    url: "https://secretmanager.googleapis.com"
    projectId: example-project

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
      secret: token

  third-party-api-token:
    vals: "ref+gcpsecrets://example-project/third-party-api-token?secret_store_id=gcp-primary"
    strategy: fail_if_absent
    data:
      secret: envgeneGenerateValue
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

Length is 32 characters.

## Behaviour

### Pre-flight phase

Structural checks on the context and the CLI environment. No network calls.

1. **Store reference in `vals` query.** When a `vals` string carries a `secret_store_id`
   query parameter, that name appears in `secretStores`.
2. **Store credentials.** Authentication variables for every store referenced in the
   context are present in the CLI environment.

On failure, the CLI logs the failure and exits non-zero. No further phase runs.

### Dry-run phase

Store authentication and per-credential prerequisite checks. No writes. This phase runs
in both apply and `--dry-run` modes.

1. **Store authentication.** For each `secretStores` entry, authenticate to the store
   using the corresponding environment variables.
2. **Per-credential check.** For each `credentials.<id>`, resolve the target store from
   the `vals` query parameter or, when absent, from the `default-store` entry in
   `secretStores`. Run the per-strategy prerequisite check from the dry-run table in
   [Strategy enum](#strategy-enum).

In `--dry-run` mode, the CLI stops after this phase. The Processing and Post-processing
phases do not run.

### Processing phase

Runs in apply mode only. For each `credentials.<id>` entry, in input order:

1. Apply the strategy per the behaviour table in [Strategy enum](#strategy-enum). When
   the strategy calls for a write, generate values for each `envgeneGenerateValue`
   marker using the default pattern for the field. Real values from `data` go through
   as is. Write the result to the store through `secret_manager`.

A single credential failure does not stop the run. The CLI keeps processing the
remaining credentials and reports the final outcome in the summary line.

### Post-processing

Runs in apply mode only. The CLI emits a summary line with counts of `created`,
`overwritten`, `skipped`, `verified`, and `failed`. The CLI exit code reflects whether
any credential failed and whether any earlier phase failed.
