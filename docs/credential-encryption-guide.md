# Credentials File Encryption Guide — Instance Project

---

## Table of Contents

- [Description](#description)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Steps](#steps)
- [Fernet Encryption Details](#fernet-encryption-details)
  - [Prerequisites (Fernet)](#prerequisites-fernet)
  - [Setup Steps (Fernet)](#steps-fernet)
  - [How It Works (Fernet)](#how-it-works-fernet)
- [SOPS Encryption Details](#sops-encryption-details)
  - [Prerequisites (SOPS)](#prerequisites-sops)
  - [Setup Steps (SOPS)](#setup-steps-sops)
  - [How It Works (SOPS)](#workflow-sops)
- [Testing Procedure](#testing-procedure)
- [Notes](#notes)


---

## Description

This guide explains **two methods of file encryption** supported in our system:

1. **[Fernet](#fernet-encryption-details)** – A symmetric encryption method using a shared secret key. Best for simple CI/CD scenarios and local development.  
2. **[SOPS (Secrets OPerationS)](https://github.com/getsops/sops)** – A more secure, KMS-integrated tool for cloud environments and multi-user collaboration.

Encryption behavior is controlled by two parameters:

- `crypt_backend`: Defines the backend used (`Fernet` or `SOPS`)  
- `crypt`: Enables (`true`) or disables (`false`) encryption

---

## Prerequisites

- **Fernet:** See [Fernet Encryption Details](#fernet-encryption-details) section  
- **SOPS:** See [SOPS Encryption Details](#sops-encryption-details) section

---

## Configuration

Update `/configuration/config.yaml`:

```yaml
# Enable encryption
crypt: true
crypt_backend: SOPS   # or Fernet

# Disable encryption
crypt: false
````

---

## Steps

1. Configure encryption flags in `/configuration/config.yaml`.

2. Encrypt files based on the selected backend (Fernet or SOPS).

3. Commit only **encrypted files ** – never secret keys.

4. Ensure CI/CD pipelines can access required keys for decryption.

---

## Fernet Encryption Details

### Prerequisites (Fernet)

  Ensure these parameters are set in `/configuration/config.yaml`:

   ```yaml
   crypt: true
   crypt_backend: Fernet
   ```

* **SECRET\_KEY:**
  Store securely as a CI/CD variable in your Instance repository.
  If missing, generate one at [fernetkeygen.com](https://fernetkeygen.com/).

* **Python Environment:**
  Python 3.6 or higher installed.

### Setup Steps (Fernet)

1. **Install Git Hooks**

   **Windows:**

   ```bash
   copy git_hooks\pre-commit .git\hooks
   ```

   **Linux/macOS:**

   ```bash
   cp git_hooks/pre-commit .git/hooks/pre-commit
   chmod a+x .git/hooks/pre-commit
   ```

2. **Set Encryption Key**
   Create `.git/secret_key.txt` and paste your encryption key. This should match the `SECRET_KEY` in your CI/CD variables.

4. **Setup Virtual Environment**

   **Windows:**

   ```bash
   python -m venv .git_hook_venv
   cd .git_hook_venv/Scripts/
   activate.bat
   python -m pip install pre-commit cryptography ruyaml ruamel.yaml jschon jschon-sort jsonschema click
   deactivate
   ```

   **Linux/macOS:**

   ```bash
   python -m venv .git_hook_venv
   source .git_hook_venv/bin/activate
   python -m pip install pre-commit cryptography ruyaml ruamel.yaml jschon jschon-sort jsonschema click
   deactivate
   ```

### How It Works  (Fernet)

 * A **pre-commit hook** automatically encrypts sensitive files before each commit.
 * On CI/CD, the encryption key is loaded from pipeline variables to enable encryption/decryption.
 * During deployment, the CI/CD pipeline reads SECRET_KEY and decrypts automatically.
 * Files are stored encrypted in Git.


---

## SOPS Encryption Details

### Prerequisites  (SOPS)

1. **Configuration:**

Ensure these parameters are set in `/configuration/config.yaml`:

   ```yaml
   crypt: true
   crypt_backend: SOPS
   ```
2. **Store Keys Securely**

 Store below Keys securely as CI/CD variables in your Instance repository.

  * **ENVGENE_AGE_PUBLIC_KEY**
  * **SOPS_AGE_KEY** 

  Follow below steps to generate above files

2. **Install SOPS CLI (Linux):**

   ```bash
   curl -Lo sops https://github.com/getsops/sops/releases/download/v3.8.1/sops-v3.8.1.linux.amd64
   chmod +x sops
   sudo mv sops /usr/local/bin/
   sops --version
   ```

3. **Install `age` and generate key pair:**

   SOPS uses `age` for encryption.

   * **Install `age`:**

     ```bash
     sudo apt update
     sudo apt install age -y
     ```

     Or download manually:

     ```bash
     curl -Lo age.tar.gz https://github.com/FiloSottile/age/releases/latest/download/age-v1.1.1-linux-amd64.tar.gz
     tar -xzf age.tar.gz
     sudo mv age/age /usr/local/bin/
     sudo mv age/age-keygen /usr/local/bin/
     ```

   * **Generate `age` key pair:**

     ```bash
     age-keygen -o private-age-key.txt
     ```

     Sample output:

     ```
     age-keygen: warning: writing secret key to a world-readable file
     Public key: age1dgtrrrz4jhgzqxqex38myjgawuyaw0vrwla5l7s0mpnnyjlwhpwqmfsf5c
     ```

   * Extract public key:

     ```bash
     age-keygen -y -i private-age-key.txt > age_public_key.txt
     ```

---

### Setup Steps (SOPS)

1. **Pre-commit Hook Setup:**

   ```bash
   cp git_hooks/pre-commit .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   ```

2. **Add age Keys:**

    Place private-age-key.txt and age_public_key.txt in `.git ` directory.
    
3. **Create Virtual Environment and Install Dependencies:**

   **Windows:**

   ```bash
   python -m venv .git_hook_venv
   cd .git_hook_venv/Scripts/
   activate.bat
   python -m pip install pre-commit cryptography ruyaml ruamel.yaml jschon jschon-sort jsonschema click
   deactivate
   ```

   **Linux/macOS:**

   ```bash
   python -m venv .git_hook_venv
   source .git_hook_venv/bin/activate
   python -m pip install pre-commit cryptography ruyaml ruamel.yaml jschon jschon-sort jsonschema click
   deactivate
   ```

---

### How It Works (SOPS)

* Make changes to files containing secrets.
* Commit changes.
* The pre-commit hook automatically encrypts files using SOPS with your `age` key.
* Only encrypted files are committed and pushed.

---

## Notes

* **Never commit private keys or secrets.**
* Ensure `crypt: true` in config for encryption to work.
* CI/CD pipeline must have access to keys for decryption.

---

## Testing Procedure

* Set `crypt: false` in `/configuration/config.yaml` and confirm files remain plaintext.
* Set `crypt: true` and verify files get encrypted correctly.
* Test both Fernet and SOPS encryption/decryption workflows with sample files.
* Confirm that secret keys or age keys are properly configured in your CI/CD environment.
* Verify pipelines decrypt files correctly during deployment.

---

## Notes

* Secret keys must **never** be committed or exposed in logs.
* Rotate encryption keys regularly.
* Automate encryption via pre-commit hooks and CI/CD for consistency.
