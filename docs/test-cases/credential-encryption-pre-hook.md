# Credential Files Encryption Using Git Commit Hook — Test Cases

- [ Credentials File Encryption Test Cases](#credentials-file-encryption-test-cases)
  - [TC-004-001: Encryption Enabled with Supported Fields](#tc-004-001-encryption-enabled-with-supported-fields)
  - [TC-004-002: Encryption Skipped When Disabled](#tc-004-002-encryption-skipped-when-disabled)
  - [TC-004-003: Secret Key Mandatory for Fernet](#tc-004-003-secret-key-mandatory-for-fernet)
  - [TC-004-004: Successful Encryption Using Fernet](#tc-004-004-successful-encryption-using-fernet)
  - [TC-004-005: Skip Encryption if File Already Encrypted Using Fernet](#tc-004-005-skip-encryption-if-file-already-encrypted-using-fernet)
  - [TC-004-006: age_key Mandatory for SOPS](#tc-004-006-age_key-mandatory-for-sops)
  - [TC-004-007: Successful Encryption Using SOPS](#tc-004-007-successful-encryption-using-sops)
  - [TC-004-008: Skip Encryption if File Already Encrypted Using SOPS](#tc-004-008-skip-encryption-if-file-already-encrypted-using-sops)

## Overview

This document defines test cases to validate credential file encryption behavior using `Fernet` and `SOPS` backends, enforced via Git pre-commit hooks.

###  How it works

Credential files are automatically encrypted during Git commits using a pre-commit script located in `.git/hooks`.

Credential files are considered valid for encryption if they match **one of the following path patterns**:
- `./*/credentials/*.y*ml`
- `./*/app-deployer/*creds*.y*ml`
- `./*/cloud-passport/*creds*.y*ml`

Encryption behavior is governed by:

- `crypt_backend`: Specifies the backend (`Fernet` or `SOPS`)
- `crypt`: Boolean flag to enable/disable encryption

Example (`/configuration/config.yaml`):

```yaml
crypt: true
crypt_backend: Fernet  # or SOPS
```

**Note:**

- `secret_key` is required for **Fernet**
- `age_public_key` is required for **SOPS**
- Corresponding keys must be available in the local `.git` directory

---

## TC-004-001: Encryption Enabled with Supported Fields

**Status:** Active

**Description:** Verify that when `crypt: true` in the configuration, only supported credential attributes (`username`, `password`, `secret`) as per [Credential Object Specification](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#credential) are encrypted using the selected backend (`Fernet` or `SOPS`).

**Test Data:**

- configuration/config.yaml
- configuration/credentials/credentials.yml

**Pre-requisites:**

1. Git pre-commit hook is installed
2. `crypt: true` in config.yaml
3. Valid credential file with supported fields
4. Appropriate encryption key available in `.git` directory (i.e., `secret_key.txt` for Fernet or `age_public_key.txt` for SOPS)

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

## TC-004-003: Secret Key Mandatory for Fernet

**Status:** Active

**Description:**  
Verify that encryption fails when `crypt_backend` is `Fernet` and `secret_key` is not provided.

**Test Data:**

- configuration/config.yaml  
- configuration/credentials/credentials.yml

**Pre-requisites:**

1. `crypt_backend: Fernet`, `crypt: true`  
2. No `.git/secret_key.txt` file exists

**Steps:**

- Modify the credential file  
- Ensure `.git/secret_key.txt` is missing  
- Run `git commit`

**Expected Results:**

- Commit fails with message:  
  `SECRET_KEY is required for Fernet encryption in ./configuration/credentials/credentials.yml`

---

## TC-004-004: Successful Encryption Using Fernet

**Status:** Active

**Description:**  
Verify that encryption succeeds when a valid `.git/secret_key.txt` is provided.  
Supported fields are encrypted per [Credential Object Specification](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#credential).

**Test Data:**

- configuration/config.yaml  
- configuration/credentials/credentials.yml  
- .git/secret_key.txt

**Pre-requisites:**

1. `crypt_backend: Fernet`, `crypt: true`  
2. Valid Fernet key in `.git/secret_key.txt`

**Steps:**

- Modify credential file  
- Stage and commit

**Expected Results:**

- `username`, `password`, `secret` fields are encrypted (e.g., `[encrypted:AES256_Fernet]...`)  
- Other fields are unchanged  
- YAML remains valid

---

## TC-004-005: Skip Encryption if File Already Encrypted Using Fernet

**Status:** Active

**Description:**  
Verify that if the credential file is already encrypted with Fernet, the encryption is skipped and warning is logged.

**Test Data:**

- `configuration/credentials/credentials.yml` (already encrypted)

**Pre-requisites:**

1. Valid encrypted credentials file  
2. `.git/secret_key.txt` available  
3. `crypt: true`, `crypt_backend: Fernet`

**Steps:**

- Stage and commit encrypted file

**Expected Results:**

- Warning logged:  
  `File already encrypted; encryption skipped. Please ensure the existing file was encrypted with the same key.`  
- File remains unchanged

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
   
    `ERROR: ENVGENE_AGE_PUBLIC_KEY is required for SOPS encryption in configuration/credentials/credentials.yml`
   

---

## TC-004-007: Successful Encryption Using SOPS

**Status:** Active

**Description:**  
Verify that credentials are encrypted using SOPS when valid age key is provided.  
Only supported fields (`username`, `password`, `secret`) are encrypted.  
See [Credential Object Specification](https://github.com/Netcracker/qubership-envgene/blob/main/docs/envgene-objects.md#credential).

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
