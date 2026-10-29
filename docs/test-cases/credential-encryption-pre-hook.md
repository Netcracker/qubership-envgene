# Credential Files Encryption Using Git Commit Hook — Test Cases

- [Credential Files Encryption Using Git Commit Hook — Test Cases](#credential-files-encryption-using-git-commit-hook--test-cases)
  - [Overview](#overview)
    - [How it works](#how-it-works)
  - [TC-004-001: Encryption Enabled with Supported Fields](#tc-004-001-encryption-enabled-with-supported-fields)
  - [TC-004-002: Encryption Skipped When Disabled](#tc-004-002-encryption-skipped-when-disabled)
  - [TC-004-006: age\_key Mandatory for SOPS](#tc-004-006-age_key-mandatory-for-sops)
  - [TC-004-007: Successful Encryption Using SOPS](#tc-004-007-successful-encryption-using-sops)
  - [TC-004-008: Skip Encryption if File Already Encrypted Using SOPS](#tc-004-008-skip-encryption-if-file-already-encrypted-using-sops)

## Overview

This document defines test cases to validate credential file encryption behavior using the `SOPS` backend, enforced via Git pre-commit hooks.

### How it works

Credential files are automatically encrypted during Git commits using a pre-commit script located in `.git/hooks`.

Credential files are considered valid for encryption if they match **one of the following path patterns**:

- `./*/credentials/*.y*ml`
- `./*/app-deployer/*creds*.y*ml`
- `./*/cloud-passport/*creds*.y*ml`

Encryption behavior is governed by:

- `crypt_backend`: Specifies the backend (`SOPS`)
- `crypt`: Boolean flag to enable/disable encryption

Example (`/configuration/config.yaml`):

```yaml
crypt: true
crypt_backend: SOPS
```

**Note:**

- `age_public_key` is required for **SOPS**
- Corresponding keys must be available in the local `.git` directory

---

## TC-004-001: Encryption Enabled with Supported Fields

**Status:** Active

**Description:** Verify that when `crypt: true` in the configuration, only supported credential attributes (`username`, `password`, `secret`) as per [Credential Object Specification](/docs/envgene-objects.md#credential) are encrypted using the `SOPS` backend.

**Test Data:**

- configuration/config.yaml
- configuration/credentials/credentials.yml

**Pre-requisites:**

1. Git pre-commit hook is installed
2. `crypt: true` in config.yaml
3. Valid credential file with supported fields
4. Appropriate encryption key available in `.git` directory (`age_public_key.txt` for SOPS)

**Steps:**

- Ensure `crypt_backend` is correctly configured
- Modify the credential file
- Run `git commit`

**Expected Results:**

- Supported fields are encrypted
- File remains valid YAML
- Non-sensitive fields are not modified

---

## TC-004-002: Encryption Skipped When Disabled

**Status:** Active

**Description:** Verify that when `crypt: false`, encryption is not performed and all fields remain in plaintext.

**Test Data:**

- configuration/config.yaml
- configuration/credentials/credentials.yml

**Pre-requisites:**

1. Git pre-commit hook is installed
2. `crypt: false` in config.yaml
3. Valid credential file with plaintext values

**Steps:**

- Set `crypt: false` in config.yaml
- Modify the credential file
- Run `git commit`

**Expected Results:**

- No fields are encrypted
- Credential file remains unchanged
- No warnings or errors related to encryption

---

## TC-004-006: age_key Mandatory for SOPS

**Status:** Active

**Description:**
Verify that encryption fails when `crypt_backend: SOPS` is used but required age_public_key is missing.

**Test Data:**

- configuration/config.yaml
- configuration/credentials/credentials.yml

**Pre-requisites:**

1. `crypt: true`, `crypt_backend: SOPS`
2. Missing `age_public_key.txt`

**Steps:**

- Modify credentials
- Stage and commit

**Expected Results:**

- Commit fails with clear message on missing key

```text
    `ERROR: ENVGENE_AGE_PUBLIC_KEY is required for SOPS encryption in configuration/credentials/credentials.yml`
```

---

## TC-004-007: Successful Encryption Using SOPS

**Status:** Active

**Description:**
Verify that credentials are encrypted using SOPS when valid age key is provided.
Only supported fields (`username`, `password`, `secret`) are encrypted.
See [Credential Object Specification](/docs/envgene-objects.md#credential).

**Test Data:**

- configuration/config.yaml
- configuration/credentials/credentials.yml
- .git/ge_public_key.txt

**Pre-requisites:**

1. SOPS encryption enabled in config
2. Valid `age_public_key` in `.git` directory

**Steps:**

- Modify credential file
- Stage and commit

**Expected Results:**

- Supported fields are encrypted with `ENC[AES256_GCM,...]`
- YAML remains valid and other fields are untouched

---

## TC-004-008: Skip Encryption if File Already Encrypted Using SOPS

**Status:** Active

**Description:**
Ensure that encryption is skipped for files already encrypted with SOPS.

**Test Data:**

- configuration/credentials/credentials.yml (already SOPS encrypted)

**Pre-requisites:**

1. `crypt: true`, `crypt_backend: SOPS`
2. Valid encrypted file
3. Valid age_public_key.txt is present

**Steps:**

- Stage and commit encrypted file

**Expected Results:**

- Warning logged:
  `File already encrypted; encryption skipped. Please ensure the existing file was encrypted with the same key.`
- File remains unchanged
