
# Credential Encryption

- [Credential Encryption](#credential-encryption)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
    - [Assumptions \& Limitation](#assumptions--limitation)
    - [Requirements](#requirements)
    - [Credentials Files](#credentials-files)
    - [Credential Flow Diagram](#credential-flow-diagram)
    - [Encryption enabling](#encryption-enabling)
      - [Impact of crypt on EnvGene's encrypt/decrypt operations](#impact-of-crypt-on-envgenes-encryptdecrypt-operations)
    - [Encryption backend](#encryption-backend)
      - [SOPS Encryption backend](#sops-encryption-backend)
      - [Fernet Encryption backend](#fernet-encryption-backend)
    - [Shade Credential Files](#shade-credential-files)
      - [Credential Files to Shade Credential Files](#credential-files-to-shade-credential-files)
      - [Shade Credential Files to Credential Files](#shade-credential-files-to-credential-files)
      - [Shade Credential Files Header](#shade-credential-files-header)

## Problem Statement

TBD

## Proposed Approach

TBD

### Assumptions & Limitation

1. Shade Credential Files are supported for `SOPS` crypt backend only
2. Credential encryption is used in Instance repository, and not used in Template repository
3. The files described in this [section](#credentials-files) contain sensitive parameters

### Requirements

1. Credentials must not be stored unencrypted in the remote repository if encryption is enabled
2. Credentials must not be stored unencrypted in the artifacts of an EnvGene job execution if encryption is enabled
3. The private key must not be located on the user's local machine
4. The files described in this [section](#credentials-files) contain Credentials
5. Only the following Credential attributes must be encrypted:
   1. `username`
   2. `password`
   3. `secret`
6. The following Credential values must not be encrypted:
   1. `envgeneNullValue`
   2. `ValueIsSet`
7. `crypt` determines whether Credentials will be encrypted
8. `crypt_backend` specifies which encryption backend to use (`Fernet` or `SOPS`)
9. `Fernet` and `SOPS` [backends](#encryption-backend) are supported
10. `crypt_create_shades` determines whether Shade Credential Files will be created
11. Shade Credential Files support is only available for the SOPS backend
12. Shade Credential Files must have the [header](#shade-credential-files-header)
13. The encrypt/decrypt function must be identical for EnvGene and the pre-commit hook

### Credentials Files

The following files are considered to contain sensitive parameters and therefore should be encrypted:

- [Environment Credentials File](/docs/envgene-objects.md#environment-credentials-file)
- [Shared Credentials File](/docs/envgene-objects.md#shared-credentials-file)
- [System Credentials File](/docs/envgene-objects.md#system-credentials-file-in-instance-repository)
- [Cloud Passport Credential File](/docs/envgene-objects.md#cloud-passport)
- [Shade Credential Files](/docs/envgene-objects.md#shade-credentials-file)

### Credential Flow Diagram

The diagram below illustrates EnvGene components and the transfer points of sensitive parameters between them where encryption and decryption of sensitive parameters occurs

![sbom-generation.png](./images/cred-encryption.png)

### Encryption enabling

The encryption functions is globally configured by a parameter defined in [`/configuration/config.yml`](/docs/envgene-configs.md#configyml):

```yaml
# Optional. Default value - `true`
crypt: boolean
```

#### Impact of crypt on EnvGene's encrypt/decrypt operations

Encryption in the following modules should only occur when `crypt: true`:

- `pre-commit hook`
- `env_inventory_generation_job`
- `generate_effective_set_job`

Encryption in `cloud_passport_cli` should always occur, regardless of the `crypt` parameter.

Decryption in the following should always occur:
  
- `cmdb_import_job` module
- `decrypt_system_cred_files` function

Decryption in the `process_decryption_mode_job` module should occur based on the `cloud_passport_decryption` parameter, but only when `crypt: true`

### Encryption backend

This parameter specifies the encryption method employed by EnvGene. The encryption backend is defined in [`/configuration/config.yml`](/docs/envgene-configs.md#configyml):

```yaml
# Optional. Default value - `Fernet`
crypt_backend: enum [`Fernet`, `SOPS`]
```

The encryption backend is a global attribute for the entire repository. For data integrity, all Credentials must be encrypted using the specified mode. A situation where one encryption mode is set, but the repository contains Credentials encrypted using a different mode is invalid

#### SOPS Encryption backend

TBD

Uses [`PUBLIC_AGE_KEYS`](/docs/instance-pipeline-parameters.md#public_age_keys) as the public key and [`ENVGENE_AGE_PRIVATE_KEY`](/docs/instance-pipeline-parameters.md#envgene_age_private_key) as the private key

#### Fernet Encryption backend

Uses [`SECRET_KEY`](/docs/instance-pipeline-parameters.md#secret_key) value as the encryption key

### Shade Credential Files

SOPS encrypts the entire file and calculates a Message Authentication Code (MAC) for it. Consequently, modifying any individual credential within a Credential File requires complete decryption and re-encryption of the entire file. This results in changes to all encrypted values, even for unchanged data, creating uninformative commits that obscure actual changes in version history.

To address this, Credential storing individually in Shade Credential files. These files are auto-generated by a pre-commit hook and contain only a single Credential.

Created for Credentials from the following files:

- [Environment Credentials File](/docs/envgene-objects.md#environment-credentials-file)
- [Shared Credentials File](/docs/envgene-objects.md#shared-credentials-file)
- [System Credentials File](/docs/envgene-objects.md#system-credentials-file-in-instance-repository)
- [Cloud Passport Credential File](/docs/envgene-objects.md#cloud-passport)

Not created for credential files in the Effective Set.

Creation mode is controlled by [`crypt_create_shades`](/docs/envgene-configs.md#configyml)

Any YAML file in the folder whose name starts with `shade` is treated as a Shade Credential File

#### Credential Files to Shade Credential Files

Occurs during every encryption if `crypt_create_shades: true`:

1. **Creation of folder for Shade Credential Files**: In the same directory as the original Credential file, a new folder is created named `shades-<Credential-file-name>`
2. **Creation of Shade Credential Files**: For each Credential from the original Credential file, a separate Shade Credential file `<Credential-ID>-cred.yml` is created
   1. If the Shade Credential file already exists, and the `type` attribute has not changed, and all values of the Credential in the original Credential file are equal to `ValueIsSet`, the existing Shade Credential file is not modified
   2. In all other cases, the existing Shade Credential file is replaced
3. **Value Replacement in Generic Credential Files**
   1. If the credential value is `ValueIsSet` or `envgeneNullValue`, no replacement occurs
   2. In all other cases, including empty values, the value is replaced with `ValueIsSet`

#### Shade Credential Files to Credential Files

Occurs during every decryption if `crypt_create_shades: true`

This reverse conversion performs the inverse operation of [`Credential Files to Shade Credential Files`](#credential-files-to-shade-credential-files) restores unencrypted values from decrypted Shade Credential files into the original Credential Files

The resulting Credential Files files contain Credentials with unencrypted values (extracted from Shade Credentials files)

These are used only for EnvGene runtime operations. Never persisted to the repository

#### Shade Credential Files Header

Each Shade Credential File includes the following header:

```yaml
# The contents of this Shade Credential File is generated from Credential: <source credential ID>
# located at <repository path to source file>
# Contents will be overwritten by next generation.
# Please modify this contents only for development purposes or as workaround.
```
