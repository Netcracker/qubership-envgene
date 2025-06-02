
# Credential Encryption

- [Credential Encryption](#credential-encryption)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
    - [Assumptions \& Limitation](#assumptions--limitation)
    - [Requirements](#requirements)
    - [`envgene-sops` Library](#envgene-sops-library)
    - [Test Cases](#test-cases)

## Problem Statement

TBD

## Proposed Approach

TBD

### Assumptions & Limitation

TBD

### Requirements

TBD

### `envgene-sops` Library

A Python library used to encrypt and decrypt Credential files using SOPS. It is invoked via pre-commit hook and during the execution of other EnvGene functions. EnvGene relies exclusively on this library for all encryption/decryption operations

The library also supports managing Shadow Credential files (creation, modification)

> [!NOTE]
> Processing a single Shadow Credential file (creating, modification, encryption/decryption) must not exceed 10ms. Full processing of a repository containing 1,000 shadow files must complete within 10 seconds

Below are the input parameters for this library:

| Attribute | Type | Mandatory | Default | Description | Example |
|---|---|---|---|---|---|
| `input-path` | string | yes | None | Path to the folder or file containing Credentials to be processed | `/environments/` or `/configuration/credentials/credentials` |
| `output-path` | string | no | None | Path to the folder where the processed file-structure (from `input-path`) will be saved. Mutually exclusive with `in-place: true` | `/tmp/environments` |
| `in-place`| boolean | no | `true` | Determines whether the processed file-structure will be saved to `output-path` (if `false`) or modified in-place in `input-path` (if `true`) | `false` |
| `encrypt`| boolean | no | `false` | If set `true`, the Credentials in the file-structure (passed via `input-path`) will be encrypted. Mutually exclusive with `decrypt: true` | `true` |
| `decrypt`| boolean | no | `false` | If set `true`, the credentials in the file structure (passed via `input-path`) will be decrypted | `true`. Mutually exclusive with `encrypt: true` |
| `sops-private-key` | string | no | None | Private key from an age key pair, used for decryption. Used with `decrypt`. Mutually exclusive with `sops-config-path` and `sops-public-key` | `AGE-SECRET-KEY-1QZ0W4QJY9W7Z0W4QJY9W7Z0W4QJY9W7Z0W4QJY9W7Z0W4QJY9W7Z0W4QJ` |
| `sops-public-key` | string | no | None | Public key from an age key pair, used for encryption. Used with `encrypt`. Mutually exclusive with `sops-config-path` and `sops-private-key` | `age1t6qt8wz07qy9w7z0w4qjy9w7z0w4qjy9w7z0w4qjy9w7z0w4qjy9w7z0w4qj` |
| `sops-config-path` | string | no | None | Path to the SOPS config file. Used for storing the private key and KMS integration cases. Mutually exclusive with `sops-private-key` and `sops-public-key` | `/configuration/sops.yaml` |

### Test Cases

  1. TBD
