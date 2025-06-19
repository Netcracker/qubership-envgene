#  Credential Files Encryption Using git commit hook Test Cases

- [ Credentials File Encryption Test Cases](#credentials-file-encryption-test-cases)
  - [TC-004-001: Common Scenario Encryption Enable/Disable](#tc-004-001-common-scenario-encryption-enabledisable)
  - [TC-004-002: Secret Key Mandatory for Fernet](#tc-004-002-secret-key-mandatory-for-fernet)
  - [TC-004-003: Successful Encryption Using Fernet](#tc-004-003-successful-encryption-using-fernet)
  - [TC-004-004: Skip Encryption if File Already Encrypted Using Fernet](#tc-004-004-skip-encryption-if-file-already-encrypted-using-fernet)
  - [TC-004-005: age_key Mandatory for SOPS](#tc-004-005-age_key-mandatory-for-sops)
  - [TC-004-006: Successful Encryption Using SOPS](#tc-004-006-successful-encryption-using-sops)
  - [TC-004-007: Skip Encryption if File Already Encrypted Using SOPS](#tc-004-007-skip-encryption-if-file-already-encrypted-using-sops)


## Overview
This document defines test cases to validate the encryption behavior for configurations using SOPS and Fernet as encryption backends using git pre-commit.

  ### How it's work

* Credential files (/*/credential.yml) automatically encrypted while commit the code with help of pre-commit script available in .git/hook folder

* Encryption behavior is controlled by two parameters:
     
- `crypt_backend`: Defines the backend used (`Fernet` or `SOPS`)  
- `crypt`: Enables (`true`) or disables (`false`) encryption

    `/configuration/config.yaml`:

```yaml
# Enable encryption
crypt: true
crypt_backend: SOPS or Fernet

# Disable encryption
crypt: false
 ```
* secret_key is require for Fernet and age_key is require for SOPS encryption         
* Corresponding secret_key or age_key should be available in .git folder in local.           

## TC-004-001: Common Scenario Encryption Enable/Disable
- **Description:** Verify that encryption only occurs if the `crypt` flag is `true`.
- **Test Steps:**
  1. Set `crypt` to `true`.
  2. commit the code.
  3. Validate that the data is encrypted available in **credentials**.yml file.
  4. Set `crypt` to `false`.
  5. commit the code.
  6. Validate that the data remains unencrypted.
- **Expected Result:**
  - Data is encrypted only when `crypt` is `true`.
  - When `crypt` is `false`, encryption does not occur and the data remains in plaintext.

---

## TC-004-002: Secret Key Mandatory for Fernet

- **Description:** Verify that `secret_key` must be provided if `crypt_backend` is set to `fernet`.

- **Test Steps:**
  1. Set `crypt_backend` to `fernet`.
  2. Do **not** provide `secret_key`.
  3. Attempt to initialize encryption.
- **Expected Result:**
  - Initialization fails with a validation error when `secret_key` is missing.

  ### input

```yaml
app-deployer-username-cred:
  type: secret
  data:
    secret: "admin"
app-deployer-token-cred:
  type: secret
  data:
    secret: "admin@1213"
```

  ### result

```bash
    ❌ ERROR: SECRET_KEY is required for Fernet encryption in ./configuration/credentials/credentials.yml
```
---

## TC-004-003: Successful Encryption Using Fernet

- **Description:** Verify that `secret_key` must be provided if `crypt_backend` is set to `fernet`.

- **Test Steps:**
  1. Set `crypt_backend` to `fernet`.
  2. add valid `secret_key` file in .git.
  3. Attempt to initialize encryption.

- **Expected Result:**
  - Encryption succeeds when a valid `secret_key` is provided.

### input

```yaml
app-deployer-username-cred:
  type: secret
  data:
    secret: "admin"
app-deployer-token-cred:
  type: secret
  data:
    secret: "admin@1213"
```

 ### result

 ```yaml
app-deployer-token-cred:
  type: secret
  data:
    secret: "[encrypted:AES256_Fernet]gAAAAABoRn9kOvOONegZrv6NhjE1uCIQvnoY3LfHQRD2fVNvU8a8mGedQgSkX8qR5oZZ6jGtxNamXEwPtMcDK2P8GMEMRLmxNg=="
app-deployer-username-cred:
  type: secret
  data:
    secret: "[encrypted:AES256_Fernet]gAAAAABoRn9kNlLWB-vAQTUX52g8mcPlIyBCLWEGnHv-KiM0vj7rXvONficSXyHTMhQZTidlM97eyZNNuaEsDWM-_1ZVPct5lw=="
```

---

## TC-004-004: Skip Encryption if File Already Encrypted Using Fernet
- **Description:** Verify that if the input file is already encrypted, encryption is skipped with a warning.
- **Test Steps:**
  1. Provide an already encrypted file.
  2. Attempt to encrypt using Fernet backend.
  3. Check for warning log/message indicating the data is already encrypted
  4. Confirm the encryption step is skipped.
- **Expected Result:**
  - System logs a warning: "File already encrypted; encryption skipped. Please ensure the existing file was encrypted with the same key.."
  - No re-encryption happens.

  input file:

```yml
app-deployer-token-cred:
  type: secret
  data:
    secret: "[encrypted:AES256_Fernet]gAAAAABoRn9kOvOONegZrv6NhjE1uCIQvnoY3LfHQRD2fVNvU8a8mGedQgSkX8qR5oZZ6jGtxNamXEwPtMcDK2P8GMEMRLmxNg=="
app-deployer-username-cred:
  type: secret
  data:
    secret: "[encrypted:AES256_Fernet]gAAAAABoRn9kNlLWB-vAQTUX52g8mcPlIyBCLWEGnHv-KiM0vj7rXvONficSXyHTMhQZTidlM97eyZNNuaEsDWM-_1ZVPct5lw=="
```


  result:

  ```bash
  Skipping ./configuration/credentials/credentials.yml — already encrypted with Fernet
  Warning: File already encrypted; encryption skipped. Please ensure the existing file was encrypted with the same key
  ```

---
## TC-004-005: age_key Mandatory for SOPS

- **Description:** Verify that `ENVGENE_AGE_PUBLIC_KEY` & `SOPS_AGE_KEY_FILE` must be provided if `crypt_backend` is set to `SOPS`.

- **Test Steps:**
  1. Set `crypt_backend` to `SOPS`.
  2. Do **not** provide age_public_key.txt & private-age-key.txt.
  3. Attempt to initialize encryption.
- **Expected Result:**
  - Initialization fails with a validation error file is missing.

  ### input

```yaml
app-deployer-username-cred:
  type: secret
  data:
    secret: "admin"
app-deployer-token-cred:
  type: secret
  data:
    secret: "admin@1213"
```

  ### result

```bash
    ❌ ERROR: ENVGENE_AGE_PUBLIC_KEY is required for SOPS encryption in ./configuration/credentials/credentials.yml
```

```bash
    ❌ ERROR: SOPS_AGE_KEY_FILE is required for SOPS encryption in ./configuration/credentials/credentials.yml
```
---

## TC-004-006: Successful Encryption Using SOPS

- **Description:** Verify that `secret_key` must be provided if `crypt_backend` is set to `SOPS`.

- **Test Steps:**
  1. Set `crypt_backend` to `SOPS`.
  2. add valid age key files in .git.
  3. Attempt to initialize encryption.

- **Expected Result:**
  - Encryption succeeds when a valid keys are provided.

### input

```yaml
app-deployer-username-cred:
  type: secret
  data:
    secret: "admin"
app-deployer-token-cred:
  type: secret
  data:
    secret: "admin@1213"
```

 ### result

 ```bash
  INFO: ./configuration/credentials/credentials.yml was encrypted with SOPS.
✅ Create a new commit with encrypted cred files
 ```
 ### encrypted file

 ```yaml
app-deployer-username-cred:
  type: secret
  data:
    secret: ENC[AES256_GCM,data:kZgBvEY=,iv:w25FTRVIrsLQiD+aPmFfy4sdxYframsFFRZVVcu4aN0=,tag:2r8PwW7xQBrF9w1EOcheoQ==,type:str]
app-deployer-token-cred:
  type: secret
  data:
    secret: ENC[AES256_GCM,data:11Rc3Uq1/8JzPg==,iv:T4zZliQmnvGHQ+t1dk9TlmSdvYDbrK58cmsNYdW0+JY=,tag:CrRZHCqrXkUz7iGre6NO3g==,type:str]
sops:
  kms: []
  gcp_kms: []
  azure_kv: []
  hc_vault: []
  age:
    - recipient: age1dgtrrrz4jhgzqxqex38myjgawuyaw0vrwla5l7s0mpnnyjlwhpwqmfsf5c
      enc: |
        -----BEGIN AGE ENCRYPTED FILE-----
        YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBCQmlSVi9SZEZSU2xrVldo
        WHF1U3FoaTBWR0M4MmpOVVh6SjU3LzM2dmdBCnF2RzVWNGdLL3VxakVOL0pmM212
        a3lFWDduVmlUcFI4VnhSZkg2OXhna1EKLS0tIG4yTHZPTmwvR2xpdXk3a1RDQk9E
        WDU2TVROWlhuckJCSmo1Q3E1QlA4UEUKRTeIw5mFT+0g+/6n8hLOmZA1DNCxMwBz
        aOSMU8kjVLwu4a17h7kQCts3l+y+WspIqkHQkVpgLFscLoODw8kaew==
        -----END AGE ENCRYPTED FILE-----
  lastmodified: "2025-06-09T08:09:37Z"
  mac: ENC[AES256_GCM,data:+gCPXkOc6uWUcQy3cT0jOHeEa6HxYTopLzcGoeSUVtQg+qoxd317jSayXh/y7CTspJeVArO8ZvxSCkC4Ie5rCoo4t7v8BH1UtaVrX1S3DrtDkyq3q4p3f4NCFZggPdGjgFc/fygmCQ7AzSuBDsbR2jciw6ZWoj48eulE2yE453k=,iv:0r9LK3cnN0jAiB2s/SF0kNTDCQYSKda4ZzoSPgocXxU=,tag:UHLbTYR9sLI0F23oJy5KvQ==,type:str]
  pgp: []
  unencrypted_regex: ^type$
  version: 3.8.1

```

---

## TC-004-007: Skip Encryption if File Already Encrypted Using SOPS
- **Description:** Verify that if the input file is already encrypted, encryption is skipped with a warning.
- **Test Steps:**
  1. Provide an already encrypted file.
  2. Attempt to encrypt using SOPS backend.
  3. Check for warning log/message indicating the data is already encrypted
  4. Confirm the encryption step is skipped.
- **Expected Result:**
  - System logs a warning: "File already encrypted; encryption skipped. Please ensure the existing file was encrypted with the same key."
  - No re-encryption happens.

  input file:

```yml
app-deployer-username-cred:
  type: secret
  data:
    secret: ENC[AES256_GCM,data:kZgBvEY=,iv:w25FTRVIrsLQiD+aPmFfy4sdxYframsFFRZVVcu4aN0=,tag:2r8PwW7xQBrF9w1EOcheoQ==,type:str]
app-deployer-token-cred:
  type: secret
  data:
    secret: ENC[AES256_GCM,data:11Rc3Uq1/8JzPg==,iv:T4zZliQmnvGHQ+t1dk9TlmSdvYDbrK58cmsNYdW0+JY=,tag:CrRZHCqrXkUz7iGre6NO3g==,type:str]
sops:
  kms: []
  gcp_kms: []
  azure_kv: []
  hc_vault: []
  age:
    - recipient: age1dgtrrrz4jhgzqxqex38myjgawuyaw0vrwla5l7s0mpnnyjlwhpwqmfsf5c
      enc: |
        -----BEGIN AGE ENCRYPTED FILE-----
        YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBCQmlSVi9SZEZSU2xrVldo
        WHF1U3FoaTBWR0M4MmpOVVh6SjU3LzM2dmdBCnF2RzVWNGdLL3VxakVOL0pmM212
        a3lFWDduVmlUcFI4VnhSZkg2OXhna1EKLS0tIG4yTHZPTmwvR2xpdXk3a1RDQk9E
        WDU2TVROWlhuckJCSmo1Q3E1QlA4UEUKRTeIw5mFT+0g+/6n8hLOmZA1DNCxMwBz
        aOSMU8kjVLwu4a17h7kQCts3l+y+WspIqkHQkVpgLFscLoODw8kaew==
        -----END AGE ENCRYPTED FILE-----
  lastmodified: "2025-06-09T08:09:37Z"
  mac: ENC[AES256_GCM,data:+gCPXkOc6uWUcQy3cT0jOHeEa6HxYTopLzcGoeSUVtQg+qoxd317jSayXh/y7CTspJeVArO8ZvxSCkC4Ie5rCoo4t7v8BH1UtaVrX1S3DrtDkyq3q4p3f4NCFZggPdGjgFc/fygmCQ7AzSuBDsbR2jciw6ZWoj48eulE2yE453k=,iv:0r9LK3cnN0jAiB2s/SF0kNTDCQYSKda4ZzoSPgocXxU=,tag:UHLbTYR9sLI0F23oJy5KvQ==,type:str]
  pgp: []
  unencrypted_regex: ^type$
  version: 3.8.1

```


  result:

  ```bash
 Skipping ./configuration/credentials/credentials.yml — already encrypted with SOPS
 Warning: File already encrypted; encryption skipped. Please ensure the existing file was encrypted with the same key. 
  ```