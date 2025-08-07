# Credential Encryption

This guide shows you how to protect sensitive credentials in your instance repository by encrypting them before committing to Git.

## Table of Contents

- [Credential Encryption](#credential-encryption)
  - [Table of Contents](#table-of-contents)
  - [How to enable Credential encryption](#how-to-enable-credential-encryption)
    - [Step 1: Install Required Tools](#step-1-install-required-tools)
    - [Step 2: Generate Encryption Keys](#step-2-generate-encryption-keys)
    - [Step 3: Configure Your Project](#step-3-configure-your-project)
    - [Step 4: Install Encryption Tools](#step-4-install-encryption-tools)
    - [Step 5: Test the Setup](#step-5-test-the-setup)
    - [Verify Your Encryption is Working](#verify-your-encryption-is-working)
    - [Troubleshooting Common Issues](#troubleshooting-common-issues)
  - [How to Migrate from Fernet to SOPS](#how-to-migrate-from-fernet-to-sops)
    - [Step 1: Prepare for Migration](#step-1-prepare-for-migration)
    - [Step 2: Set Up SOPS](#step-2-set-up-sops)
    - [Step 3: Update Configuration](#step-3-update-configuration)
    - [Step 4: Re-encrypt Files](#step-4-re-encrypt-files)
    - [Step 5: Update CI/CD Variables](#step-5-update-cicd-variables)
    - [Step 6: Test Migration](#step-6-test-migration)

## How to enable Credential encryption

Use this guide when you need to enable [Credential](/docs/envgene-objects.md#credential) encryption with SOPS in Instance repository

### Step 1: Install Required Tools

1. **Install SOPS CLI**:

   ```bash
   curl -Lo sops https://github.com/getsops/sops/releases/download/v3.8.1/sops-v3.8.1.linux.amd64
   chmod +x sops
   sudo mv sops /usr/local/bin/
   sops --version
   ```

2. **Install age encryption tool**:

   ```bash
   sudo apt update
   sudo apt install age -y
   ```

   Or install manually:

   ```bash
   curl -Lo age.tar.gz https://github.com/FiloSottile/age/releases/latest/download/age-v1.1.1-linux-amd64.tar.gz
   tar -xzf age.tar.gz
   sudo mv age/age /usr/local/bin/
   sudo mv age/age-keygen /usr/local/bin/
   ```

### Step 2: Generate Encryption Keys

1. **Create your key pair**:

   ```bash
   age-keygen -o private-age-key.txt
   ```

   You'll see output like:

   ```text
   Public key: age1dgtrrrz4jhgzqxqex38myjgawuyaw0vrwla5l7s0mpnnyjlwhpwqmfsf5c
   ```

2. **Extract the public key**:

   ```bash
   age-keygen -y -i private-age-key.txt > age_public_key.txt
   ```

3. **Store keys securely**:

   - Add [`PUBLIC_AGE_KEYS`](/docs/envgene-repository-variables.md#public_age_keys) to your CI/CD variables (content of age_public_key.txt)
   - Add [`ENVGENE_AGE_PRIVATE_KEY`](/docs/envgene-repository-variables.md#envgene_age_private_key) to your CI/CD variables (content of private-age-key.txt)
   - Mark both as protected/masked

### Step 3: Configure Your Project

1. **Enable SOPS encryption** in `/configuration/config.yaml`:

   ```yaml
   crypt: true
   crypt_backend: SOPS
   ```

2. **Place key files locally**:

   - Copy `private-age-key.txt` to `.git/` directory
   - Copy `age_public_key.txt` to `.git/` directory
   - These files are ignored by Git and stay on your machine only

### Step 4: Install Encryption Tools

1. **Set up the pre-commit hook**:

   ```bash
   cp git_hooks/pre-commit .git/hooks/pre-commit
   chmod +x .git/hooks/pre-commit
   ```

2. **Install Python dependencies**:

   **Windows:**

   ```bash
   python -m venv .git_hook_venv
   .git_hook_venv\Scripts\activate
   pip install cryptography ruyaml ruamel.yaml jschon jschon-sort jsonschema click
   deactivate
   ```

   **Linux/macOS:**

   ```bash
   python -m venv .git_hook_venv
   source .git_hook_venv/bin/activate
   pip install cryptography ruyaml ruamel.yaml jschon jschon-sort jsonschema click
   deactivate
   ```

### Step 5: Test the Setup

1. **Make a test commit**:

   - Edit a credentials file
   - Run `git add` and `git commit`
   - The pre-commit hook should encrypt your files using SOPS

2. **Verify encryption worked**:

   - Check that Credentials in the repository are contain SOPS-encrypted content
   - Your local files remain readable for development

### Verify Your Encryption is Working

After setting up either Fernet or SOPS, test that everything works correctly:

### Troubleshooting Common Issues

**Files not getting encrypted:**

- Check that `crypt: true` is set in `/configuration/config.yaml`
- Verify the pre-commit hook is executable
- Ensure your encryption keys are in the correct location

**CI/CD pipeline fails:**

- Confirm your encryption keys are properly set as CI/CD variables
- Check that variable names match exactly (`PUBLIC_AGE_KEYS` and `ENVGENE_AGE_PRIVATE_KEY`)
- Verify variables are marked as protected/masked

**Local development issues:**

- Ensure your local key files are in the `.git/` directory
- Check that Python dependencies are installed in the virtual environment
- Verify file permissions on the pre-commit hook

## How to Migrate from Fernet to SOPS

If you're currently using Fernet encryption and want to upgrade to SOPS (recommended for EnvGene), follow these steps:

### Step 1: Prepare for Migration

1. **Backup your current setup**:
   - Create a backup branch: `git checkout -b backup-fernet-encryption`
   - Commit current state: `git commit -m "Backup before SOPS migration"`

2. **Decrypt all Fernet-encrypted files**:
   First, ensure you have the Fernet secret key available:

   ```bash
   # Make sure the secret key is in the .git directory
   # The key should be in .git/secret_key.txt
   ```

   Then decrypt each credentials file using the internal script:

   ```bash
   # Set environment variables
   export ENV_NAME=<your_env_name>
   export SECRET_KEY=$(cat .git/secret_key.txt)
   
   # Decrypt each credentials file
   python3 git_hooks/crypt.py decrypt_cred_file -f <path-to-cred-file> -s $SECRET_KEY
   
   # Example for multiple files:
   python3 git_hooks/crypt.py decrypt_cred_file -f environments/<cloud-name>/<env-name>/Inventory/credentials/dev-creds.yaml -s $SECRET_KEY
   python3 git_hooks/crypt.py decrypt_cred_file -f environments/<cloud-name>/<env-name>/Inventory/credentials/staging-creds.yaml -s $SECRET_KEY
   python3 git_hooks/crypt.py decrypt_cred_file -f environments/<cloud-name>/<env-name>/Inventory/credentials/prod-creds.yaml -s $SECRET_KEY
   ```

   **Windows users:**

   ```cmd
   # Set environment variables
   set ENV_NAME=<your_env_name>
   set /p SECRET_KEY=<.git\secret_key.txt
   
   # Decrypt each credentials file
   python git_hooks\crypt.py decrypt_cred_file -f <path-to-cred-file> -s %SECRET_KEY%
   ```

   Verify all credential files are now in readable format (plain text, not encrypted).

### Step 2: Set Up SOPS

1. **Follow the SOPS setup steps** described in the [How to enable Credential encryption](#how-to-enable-credential-encryption) section above
2. **Generate age keys** and store them in CI/CD variables
3. **Install SOPS tools** and dependencies

### Step 3: Update Configuration

1. **Change encryption backend** in `/configuration/config.yaml`:

   ```yaml
   crypt: true  # Re-enable encryption
   crypt_backend: SOPS  # Changed from Fernet
   ```

2. **Remove Fernet key file**:

   ```bash
   rm .git/secret_key.txt
   ```

3. **Add SOPS age keys**:

   - Place `private-age-key.txt` in `.git/` directory
   - Place `age_public_key.txt` in `.git/` directory

### Step 4: Re-encrypt Files

1. **Test the new setup** with a single file first:

   ```bash
   git add environments/<cloud-name>/<env-name>/Inventory/credentials//test.yml
   git commit -m "Test SOPS encryption"
   ```

2. **Verify SOPS encryption worked**:

   - Check that the committed file contains SOPS-encrypted content
   - Look for `sops:` metadata in the encrypted file

3. **Re-encrypt all credential files**:

   ```bash
   git add environments/<cloud-name>/<env-name>/Inventory/credentials/
   git commit -m "Migrate all credentials to SOPS encryption"
   ```

### Step 5: Update CI/CD Variables

1. **Remove old Fernet variables**:
   - Delete `SECRET_KEY` from CI/CD variables

2. **Verify SOPS variables are set**:
   - Confirm `PUBLIC_AGE_KEYS` is set
   - Confirm `ENVGENE_AGE_PRIVATE_KEY` is set
   - Both should be marked as protected/masked

### Step 6: Test Migration

1. **Push changes** and trigger CI/CD pipeline
2. **Verify pipeline works** with SOPS decryption
3. **Test in all environments** (dev, staging, prod)
4. **Delete backup branch** once migration is confirmed successful:

   ```bash
   git branch -d backup-fernet-encryption
   ```
