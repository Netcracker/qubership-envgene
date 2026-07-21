# qubership-external-cred-provision

Command-line tool for [EnvGene](https://github.com/Netcracker/qubership-envgene/blob/main/README.md) that provisions external credentials into secret stores
from a declarative YAML context file.

EnvGene generates the context during Effective Set calculation. This CLI reads that file, connects
to the configured stores, and creates or verifies secrets according to each entry's strategy. It
supports dry-run mode for CI validation without writes.

## Features

- Provisions credentials into HashiCorp Vault, OpenBao, Azure Key Vault, Google Cloud Secret Manager,
  and AWS Secrets Manager
- Idempotent strategies: verify presence, create when absent, or overwrite
- Generates secret values when a field is marked with the reserved `_generateValue` marker
- Dry-run mode for pre-flight checks before apply
- Structured logging to console and log files

## Requirements

- Python 3.12
- Network access to the target secret stores
- Store authentication via process environment variables (see
  [configuration](#configuration))
- Runtime dependency on `qubership-pipelines-common-library` for secret-store integration

## Installation

```bash
pip install qubership-external-cred-provision
```

The installed command is `external-cred-provision` (shorter than the PyPI package name).

## Quick start

Apply provisioning from a context file:

```bash
external-cred-provision path/to/external-credentials.yaml
```

Validate without writing to any store:

```bash
external-cred-provision --dry-run path/to/external-credentials.yaml
```

Set console log verbosity (full diagnostic log is always written to `full.log`):

```bash
external-cred-provision --log-level INFO path/to/external-credentials.yaml
```

## Command-line options

| Flag            | Default | Meaning                                     |
|-----------------|---------|---------------------------------------------|
| `--dry-run`     | off     | Run checks only; no writes to secret stores |
| `--log-level`   | DEBUG   | Console and `module.log` verbosity          |

Positional argument `<context-path>` is required. It must point to a YAML file that defines a
top-level `credentials` map.

## Supported secret stores

Store type is inferred from each credential's VALS reference scheme:

| VALS scheme prefix     | Store                         |
|------------------------|-------------------------------|
| `ref+vault://`         | HashiCorp Vault               |
| `ref+openbao://`       | OpenBao                       |
| `ref+azurekeyvault://` | Azure Key Vault               |
| `ref+gcpsecrets://`    | Google Cloud Secret Manager   |
| `ref+awssecrets://`    | AWS Secrets Manager           |

## Provisioning strategies

| Strategy           | Secret exists | Secret absent |
|--------------------|---------------|---------------|
| `fail_if_absent`   | skip          | fail          |
| `create_if_absent` | skip          | create        |
| `overwrite`        | overwrite     | create        |

Entries with `fail_if_absent` omit `data` because the CLI performs no write. Write strategies
require a `data` field (map or scalar, depending on the store).

## Minimal context example

```yaml
credentials:
  app-cred:
    vals: "ref+vault://kv/path/to/app-cred"
    strategy: create_if_absent
    data:
      username: app_user
      password: _generateValue

  monitoring-token:
    vals: "ref+vault://kv/path/to/monitoring-token"
    strategy: fail_if_absent
```

## Configuration

Authentication and store settings are read from environment variables. Variable names depend on
store type and optional `secret_store_id` query parameters in each VALS reference.

See the [External Credentials provisioning CLI](https://github.com/Netcracker/qubership-envgene/blob/main/docs/features/external-creds-provisioning-cli.md)
reference for the full variable list, input schema, value-generation rules, and runtime behaviour.

Broader EnvGene external-credentials design (context generation, Effective Set integration):

[External Credentials Management](https://github.com/Netcracker/qubership-envgene/blob/main/docs/features/external-creds.md)

## License

Apache License 2.0. See the [LICENSE](https://github.com/Netcracker/qubership-envgene/blob/main/LICENSE) file in the EnvGene repository.
