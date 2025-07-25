
# Credential Encryption

- [Credential Encryption](#credential-encryption)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
    - [Use cases](#use-cases)
    - [Assumptions \& Limitation](#assumptions--limitation)
    - [Requirements](#requirements)
    - [Credential Flow Diagram](#credential-flow-diagram)
      - [Impact of `crypt` on EnvGene's encrypt/decrypt operations](#impact-of-crypt-on-envgenes-encryptdecrypt-operations)
    - [Credentials Files](#credentials-files)
      - [Repository Credential Files](#repository-credential-files)
      - [Shade Credential Files](#shade-credential-files)
      - [Effective Set Credential Files](#effective-set-credential-files)
    - [Credential Encryption Marker](#credential-encryption-marker)
      - [SOPS Backend](#sops-backend)
      - [Fernet Backend](#fernet-backend)
    - [Encryption enabling](#encryption-enabling)
    - [Encryption backend](#encryption-backend)
      - [SOPS Encryption backend](#sops-encryption-backend)
      - [Fernet Encryption backend](#fernet-encryption-backend)
    - [Shade Credentials](#shade-credentials)
      - [Credential Files to Shade Credential Files](#credential-files-to-shade-credential-files)
      - [Shade Credential Files to Credential Files](#shade-credential-files-to-credential-files)
      - [Shade Credential Files Header](#shade-credential-files-header)
    - [Local Pre Commit Hook](#local-pre-commit-hook)
    - [GitLab Server-side Git Hooks](#gitlab-server-side-git-hooks)
      - [Enabling the hook in repository](#enabling-the-hook-in-repository)
      - [Hook triggers](#hook-triggers)
      - [Hook Workflow](#hook-workflow)
      - [User Notification](#user-notification)
    - [Instance-Discovery repositories integration](#instance-discovery-repositories-integration)

## Problem Statement

Энвген 

## Proposed Approach

TBD

### Use cases

1. Enabling encryption (incl. GitLab server-side hook enabling)
   1. In the Instance repository
   2. In the Discovery repository
2. Preparing the user's local machine (for running the local pre-commit hook)
3. Adding a sensitive parameter
4. Modifying the value of a sensitive parameter
5. Migrating from Fernet to SOPS
   1. in the instance repository
   2. in the discovery repository

### Assumptions & Limitation

1. [Shade Credentials](#shade-credentials) is compatible only with the `SOPS` backend.
2. Credential encryption functionality is enabled within the Instance and Discovery repositories. Template repositories do not utilize credential encryption.
3. All files referenced in the [Credentials Files](#credentials-files) section are considered to contain sensitive information and must be handled accordingly.
4. The GitLab server-side hook does not perform validation for unencrypted parameters during the creation of a Merge Request.
5. The GitLab server-side Git hook is compatible only with the `SOPS` cryptographic backend.
6. Processing is restricted to shared credential files whose paths conform to the following directory patterns:
   1. `/environments/*/*/Inventory/credentials/*.y*ml`
   2. `/environments/*/credentials/*.y*ml`
   3. `/environments/credentials/*.y*ml`

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
8. Repository encryption can be enabled in
   1. Instance repository
   2. Template repository
9. `crypt_backend` specifies which encryption backend to use (`Fernet` or `SOPS`)
10. `Fernet` and `SOPS` [backends](#encryption-backend) are supported
11. `crypt_create_shades` determines whether Shade Credential Files will be created
12. Shade Credential Files support is only available for the SOPS backend
13. Shade Credential Files must have the [header](#shade-credential-files-header)
14. The encrypt function must be identical for EnvGene and the pre-commit hook
15. In a repository containing 1000 Credential objects across 100 Credential files, the server-side GitLab hook and the local pre-commit must complete within 15 seconds

### Credential Flow Diagram

The diagram below illustrates EnvGene components and the transfer points of sensitive parameters between them where encryption and decryption of sensitive parameters occurs

![cred-encryption.png](/docs/images/cred-encryption.png)

#### Impact of `crypt` on EnvGene's encrypt/decrypt operations

TBD

<!-- энкрипта/декрипта быть не должно когда `crypt: false`

Encryption in the following modules should only occur when `crypt: true`:

- `pre-commit hook`
- `env_inventory_generation_job`
- `generate_effective_set_job`

Encryption in `cloud_passport_cli` should always occur, regardless of the `crypt` parameter.

Decryption in the following should always occur:
  
- `cmdb_import_job` module
- `decrypt_system_cred_files` function

Decryption in the `process_decryption_mode_job` module should occur based on the `cloud_passport_decryption` parameter, but only when `crypt: true` -->

### Credentials Files

This section describes which files are considered to contain sensitive parameters and therefore must be encrypted.
Credential objects in these files must conform to [credential.schema.json](/schemas/credential.schema.json).

#### Repository Credential Files

- Contain [Credential objects](/docs/envgene-objects.md#credential)
- Shade credentials are created for them if shade mode is enabled (SOPS backend only)
- When shade mode is enabled, sensitive values are replaced with `ValueIsSet` in these files and therefore **are not encrypted**
- Both SOPS and Fernet encryption backends are supported

Includes:

- [Environment Credentials File](/docs/envgene-objects.md#environment-credentials-file)
- [Shared Credentials File](/docs/envgene-objects.md#shared-credentials-file)
- [System Credentials File](/docs/envgene-objects.md#system-credentials-file-in-instance-repository)
- [Cloud Passport Credential File](/docs/envgene-objects.md#cloud-passport)

**Path patterns:**

```text
/environments/*/*/Credentials/credentials.y*ml
/environments/*/*/Inventory/credentials/*.y*ml
/environments/*/credentials/*.y*ml
/environments/credentials/*.y*ml
/configuration/credentials/*.y*ml
/environments/*/app-deployer/*-creds.y*ml
/environments/*/cloud-passport/*-creds.y*ml
```

#### Shade Credential Files

- Contain [Credential objects](/docs/envgene-objects.md#credential)
- Auto-generated from [Repository Credential Files](#repository-credential-files) if shade mode is enabled (SOPS backend only)
- Each file contains a single credential object, named `<Credential-ID>-cred.yml`, in a folder starting with `shades-`
- Not created for Effective Set Credential Files

**Path patterns:**

```text
/environments/*/*/Credentials/shades-*/**/*.y*ml
/environments/*/*/Inventory/credentials/shades-*/**/*.y*ml
/environments/*/credentials/shades-*/**/*.y*ml
/environments/credentials/shades-*/**/*.y*ml
/configuration/credentials/shades-*/**/*.y*ml
/environments/*/app-deployer/shades-*/**/*.y*ml
/environments/*/cloud-passport/shades-*/**/*.y*ml
```

See details in [Shade Credential Files](#shade-credential-files)

#### Effective Set Credential Files

- Do **not** contain [Credential objects](/docs/envgene-objects.md#credential)
- Shade credentials are **not** created for these files
- Both SOPS and Fernet encryption backends are supported

**Path patterns:**

```text
/environments/<cluster-name>/<environment-name>/effective-set/topology/credentials.yaml
/environments/<cluster-name>/<environment-name>/effective-set/pipeline/credentials.yaml
/environments/<cluster-name>/<environment-name>/effective-set/pipeline/<consumer-name>-credentials.yaml
/environments/<cluster-name>/<environment-name>/effective-set/deployment/<deployPostfix>/<application-name>/credentials.yaml
/environments/<cluster-name>/<environment-name>/effective-set/deployment/<deployPostfix>/<application-name>/collision-credentials.yaml
/environments/<cluster-name>/<environment-name>/effective-set/runtime/<deployPostfix>/<application-name>/credentials.yaml
```

### Credential Encryption Marker

#### SOPS Backend

For **[Repository Credential Files](#repository-credential-files)**:

- The `username`, `password`, and `secret` attributes of [Credential objects](/schemas/credential.schema.json) must have one of the following values:
  - `envgeneNullValue` **or**
  - `ValueIsSet` **or**
  - Match the pattern `ENC[.*]` (encrypted value)

Example:

```yaml
---
# Valid
cred-1:
  type: "usernamePassword"
  data:
    username: "envgeneNullValue"
    password: "envgeneNullValue"
cred-2:
  type: "secret"
  data:
    secret: "ValueIsSet"
cred-3:
  type: "usernamePassword"
  data:
    username: ENC[AES256_GCM,data:vSeyQwN1Z9k=,iv:DBmuX4w6w14Z/1b820OE3SM3MPx3oLGAeSoR4CWxdhg=,tag:ClpJZLb4ObIOdDD441clrw==,type:str]
    password: ENC[AES256_GCM,data:b0Y=,iv:7Ar/Tb7XCDo5ABZNdSNBqGquaGEQF7dNxd1VvW7Nwak=,tag:uEjmOKwPlkYSq4IV1tQjwQ==,type:str]
---
# Invalid
cred-1:
  type: "usernamePassword"
  data:
    username: username
    password: password
cred-2:
  type: "secret"
  data:
    secret: secret
```

For **[Shade Credential Files](#shade-credential-files)**:

- The `username`, `password`, and `secret` attributes of [Credential objects](/schemas/credential.schema.json) must have one of the following values:
  - Match the pattern `ENC[.*]` (encrypted value).

Example:

```yaml
---
# Valid
cred-1:
  type: "usernamePassword"
  data:
    username: "envgeneNullValue"
    password: "envgeneNullValue"
cred-3:
  type: "usernamePassword"
  data:
    username: ENC[AES256_GCM,data:vSeyQwN1Z9k=,iv:DBmuX4w6w14Z/1b820OE3SM3MPx3oLGAeSoR4CWxdhg=,tag:ClpJZLb4ObIOdDD441clrw==,type:str]
    password: ENC[AES256_GCM,data:b0Y=,iv:7Ar/Tb7XCDo5ABZNdSNBqGquaGEQF7dNxd1VvW7Nwak=,tag:uEjmOKwPlkYSq4IV1tQjwQ==,type:str]
---
# Invalid
cred-1:
  type: "usernamePassword"
  data:
    username: username
    password: password
cred-2:
  type: "secret"
  data:
    secret: secret
```

For **[Effective Set Credential Files](#effective-set-credential-files)**:

- Every non-object value (i.e., string, number, or boolean) must be either:
  - `envgeneNullValue` **or**
  - Match the pattern `ENC[.*]` (encrypted value).

Example:

```yaml
---
# Valid
complex_key:
  - username: ENC[AES256_GCM,data:vSeyQwN1Z9k=,iv:DBmuX4w6w14Z/1b820OE3SM3MPx3oLGAeSoR4CWxdhg=,tag:ClpJZLb4ObIOdDD441clrw==,type:str]
    password: ENC[AES256_GCM,data:b0Y=,iv:7Ar/Tb7XCDo5ABZNdSNBqGquaGEQF7dNxd1VvW7Nwak=,tag:uEjmOKwPlkYSq4IV1tQjwQ==,type:str]
  - username: ENC[AES256_GCM,data:vSeyQwN1Z9k=,iv:DBmuX4w6w14Z/1b820OE3SM3MPx3oLGAeSoR4CWxdhg=,tag:ClpJZLb4ObIOdDD441clrw==,type:str]
    password: ENC[AES256_GCM,data:b0Y=,iv:7Ar/Tb7XCDo5ABZNdSNBqGquaGEQF7dNxd1VvW7Nwak=,tag:uEjmOKwPlkYSq4IV1tQjwQ==,type:str]
secret: "envgeneNullValue"
---
# Invalid
complex_key:
  - username: username
    password: password
  - username: username
    password: password
secret: secret
```

#### Fernet Backend

TBD

### Encryption enabling

The encryption functions is globally configured by a parameter defined in [`/configuration/config.yml`](/docs/envgene-configs.md#configyml):

```yaml
# Optional. Default value - `true`
crypt: boolean
```

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

TBD

Uses [`SECRET_KEY`](/docs/instance-pipeline-parameters.md#secret_key) value as the encryption key

### Shade Credentials

SOPS encrypts the entire file and calculates a Message Authentication Code (MAC) for it. Consequently, modifying any individual credential within a Credential File requires complete decryption and re-encryption of the entire file. This results in changes to all encrypted values, even for unchanged data, creating uninformative commits that obscure actual changes in version history.

To address this, Credential storing individually in Shade Credential files. These files are auto-generated by a pre-commit hook and contain only a single Credential.

Created for [Repository Credential Files](#repository-credential-files)

Not created for [Effective Set Credential Files](#effective-set-credential-files)

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

### Local Pre Commit Hook

Sensitive parameter values enter the git repository through user commits and pushes. When encryption is enabled, the local pre-commit hook ensures these values are properly encrypted before being committed to the repository.

TBD

### GitLab Server-side Git Hooks

This server-side hook is designed to prevent publishing unencrypted sensitive parameter values in the remote EnvGene Instance repository. Encryption should occur on the user's local machine, but if encryption fails for any reason, the server-side hook will reject any commit that contains unencrypted sensitive data.

**In a repository containing 1000 Credential objects across 100 files, the hook must complete within 15 seconds**

#### Enabling the hook in repository

The hook should be triggered in each repository where the following CICD variable is set:

`CRED_ENCRYPTION_VALIDATION_HOOK_ENABLED: true`

#### Hook triggers

The hook runs on any push to the repository before applying changes.

The hook runs on the following events:

1. Push to remote repo from local
2. Changes via Web IDE
3. Changes via API

#### Hook Workflow

1. Determine whether encryption is [enabled](/docs/envgene-configs.md#configyml) in the repository.
   1. If encryption is enabled, proceed to the next step. If encryption is disabled, allow the commit.
2. Determine the [encryption backend](/docs/envgene-configs.md#configyml) in use.
   1. If the backend is `SOPS`, proceed to the next step. If the backend is `Fernet`, allow the commit.
3. Identify the list of files that have been changed in the commit.
4. Filter the changed files to include only those whose paths match the following patterns:
    1. [Repository Credential Files](#repository-credential-files)
    2. [Shade Credential Files](#shade-credential-files)
    3. [Effective Set Credential Files](#effective-set-credential-files)
5. For each file identified in the previous step, verify that all sensitive parameters are encrypted in accordance with the [Credential Encryption Marker](#sops-backend) and according to their type (Repository Credential Files, Shade Credential Files, or Effective Set Credential Files).
    1. If any sensitive parameters object is not encrypted:
       1. Terminate the process with a non-zero exit code.
       2. Output to stderr:
          1. The path to the file containing the unencrypted credential.
          2. The ID of the unencrypted credential.
    2. If all sensitive parameters objects are encrypted, allow the commit.

#### User Notification

When hook validation fails, the user receives notification depending on how the commit is made:

If via **git push**, i.e., when the user pushes changes from local repo copy, notification occurs through git console.

If via **Web IDE commit**, i.e., when the user makes changes through GitLab UI, the user is notified through a popup message with error text.

### Instance-Discovery repositories integration

TBD
