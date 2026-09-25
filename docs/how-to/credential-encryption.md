# Credential Encryption

This guide shows you how to protect sensitive credentials in your instance repository by encrypting them before committing to Git.

## Table of Contents

- [Credential Encryption](#credential-encryption)
   - [Table of Contents](#table-of-contents)
   - [Running this guide](#running-this-guide)
   - [Required Environment Variables](#required-environment-variables)
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

## Running this guide

**No installation needed** — run with `npx`. Fill in your values using the template in [Required Inputs](#required-inputs), save to any file (e.g. `my-inputs.txt`), then run:

`(set -a; source my-inputs.txt; npx runme run --all --filename credential-encryption.md)`

See [How to run guides with runme](/docs/how-to/how-to-run-guides-with-runme.md) for full CLI, VS Code, pipeline, and AI agent instructions.

Steps marked **Manual step — cannot be automated** are blockquotes — runme skips them automatically.

## Required Inputs

Create a file with your values (any filename, e.g. `my-inputs.txt`) and load it with `source` before running.

| Variable | Required | Example | Description |
|---|---|---|---|
| `CRED_MODE` | Yes | `enable` | Which flow to run: `enable` (new SOPS setup) or `migrate` (Fernet → SOPS migration) |
| `CLOUD_NAME` | Yes | `prod-cluster` | Cloud/cluster directory name under `environments/` |
| `ENV_NAME` | Yes | `prod-env-01` | Environment directory name under `environments/<cloud>/` |
| `CRED_FILE` | Yes | `dev-creds.yaml` | Credential file name under `Inventory/credentials/` |
| `OS_TYPE` | No | `linux` | Operating system for Python venv step: `linux` (default) or `windows` |

**Template** — copy, fill in your values, save as any filename:

```bash {"excludeFromRunAll":"true","name":"input-template"}
CRED_MODE=enable
CLOUD_NAME=my-cloud
ENV_NAME=my-env
CRED_FILE=dev-creds.yaml
OS_TYPE=linux
```

Validate inputs (first runnable cell — fails immediately if a required variable is missing):

```bash
# validate-inputs
: "${CRED_MODE:?CRED_MODE is required — set to 'enable' or 'migrate'}"
case "$CRED_MODE" in
  enable|migrate) echo "Mode: $CRED_MODE" ;;
  *) echo "ERROR: CRED_MODE must be 'enable' or 'migrate'"; exit 1 ;;
esac
: "${CLOUD_NAME:?CLOUD_NAME is required — see Required Inputs section}"
: "${ENV_NAME:?ENV_NAME is required — see Required Inputs section}"
: "${CRED_FILE:?CRED_FILE is required — see Required Inputs section}"
OS_TYPE="${OS_TYPE:-linux}"
echo "Inputs OK: CRED_MODE=$CRED_MODE  CLOUD_NAME=$CLOUD_NAME  ENV_NAME=$ENV_NAME  CRED_FILE=$CRED_FILE  OS_TYPE=$OS_TYPE"
```

## How to enable Credential encryption

Use this guide when you need to enable [Credential](/docs/envgene-objects.md#credential) encryption with SOPS in Instance repository

### Step 1: Install Required Tools

1. **Install SOPS CLI**:

```bash
curl -Lo sops https://github.com/getsops/sops/releases/download/v3.8.1/sops-v3.8.1.linux.amd64
chmod +x sops
sudo mv sops /usr/local/bin/
sops --version
# Expected: sops 3.8.1
```

2. **Install age encryption tool**:

```bash
sudo apt update
sudo apt install age -y
```

Or install manually (use instead of apt if your system does not have apt):

```bash {"excludeFromRunAll":"true"}
curl -Lo age.tar.gz https://github.com/FiloSottile/age/releases/latest/download/age-v1.1.1-linux-amd64.tar.gz
tar -xzf age.tar.gz
sudo mv age/age /usr/local/bin/
sudo mv age/age-keygen /usr/local/bin/
```

### Step 2: Generate Encryption Keys

1. **Create your key pair**:

```bash
if [ "$CRED_MODE" != "enable" ]; then echo "Enable mode not selected — skipping"; exit 0; fi
if [ -f "private-age-key.txt" ]; then
  echo "private-age-key.txt already exists — skipping key generation (delete it to regenerate)"
else
  age-keygen -o private-age-key.txt
fi
```

You'll see output like:

```text {"excludeFromRunAll":"true"}
Public key: age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

2. **Extract the public key**:

```bash
if [ "$CRED_MODE" != "enable" ]; then echo "Enable mode not selected — skipping"; exit 0; fi
age-keygen -y private-age-key.txt > age_public_key.txt
cat age_public_key.txt
# Expected: age1... public key string
```

3. **Store keys securely**:

   > **Manual step — cannot be automated:** Add the following CI/CD variables via the GitLab project
   > **Settings → CI/CD → Variables** UI. Mark both as **Protected** and **Masked**.
>
   > - [`PUBLIC_AGE_KEYS`](/docs/envgene-repository-variables.md#public_age_keys) — paste the content of `age_public_key.txt`
   > - [`ENVGENE_AGE_PRIVATE_KEY`](/docs/envgene-repository-variables.md#envgene_age_private_key) — paste the content of `private-age-key.txt`

### Step 3: Configure Your Project

1. **Enable SOPS encryption** in `/configuration/config.yaml`:

```bash
if [ "$CRED_MODE" != "enable" ]; then echo "Enable mode not selected — skipping"; exit 0; fi
CONFIG_FILE=""
if [ -f "configuration/config.yaml" ]; then CONFIG_FILE="configuration/config.yaml"; fi
if [ -f "configuration/config.yml" ]; then CONFIG_FILE="configuration/config.yml"; fi
if [ -z "$CONFIG_FILE" ]; then
  CONFIG_FILE="configuration/config.yaml"
  mkdir -p configuration
  printf 'crypt: true\ncrypt_backend: SOPS\n' > "$CONFIG_FILE"
  echo "Created $CONFIG_FILE"
else
  echo "Found: $CONFIG_FILE"
  if grep -q "^crypt:" "$CONFIG_FILE"; then
    sed -i 's/^crypt:.*/crypt: true/' "$CONFIG_FILE"
  else
    echo "crypt: true" >> "$CONFIG_FILE"
  fi
  if grep -qE "^#?crypt_backend:" "$CONFIG_FILE"; then
    sed -i -E 's/^#?crypt_backend:.*/crypt_backend: SOPS/' "$CONFIG_FILE"
  else
    echo "crypt_backend: SOPS" >> "$CONFIG_FILE"
  fi
fi
grep -E "^crypt" "$CONFIG_FILE"
# Expected: crypt: true  and  crypt_backend: SOPS
```

2. **Place key files in `.git/`** (ignored by Git, stay on your machine only):

```bash
if [ "$CRED_MODE" != "enable" ]; then echo "Enable mode not selected — skipping"; exit 0; fi
cp private-age-key.txt .git/private-age-key.txt
cp age_public_key.txt .git/age_public_key.txt
echo "Key files placed in .git/"
ls .git/private-age-key.txt .git/age_public_key.txt
# Expected: both files listed without error
```

### Step 4: Install Encryption Tools

1. **Set up the pre-commit hook**:

```bash
if [ "$CRED_MODE" != "enable" ]; then echo "Enable mode not selected — skipping"; exit 0; fi
cp git_hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Verify the hook is installed and executable:

```bash
if [ "$CRED_MODE" != "enable" ]; then echo "Enable mode not selected — skipping"; exit 0; fi
ls -l .git/hooks/pre-commit
# Expected: -rwxr-xr-x ... .git/hooks/pre-commit
```

2. **Install Python dependencies**:

**Windows:**

```bash
if [ "$CRED_MODE" != "enable" ]; then echo "Enable mode not selected — skipping"; exit 0; fi
if [ "$OS_TYPE" != "windows" ]; then echo "Windows venv — skipping on non-Windows OS"; exit 0; fi
if [ ! -d ".git_hook_venv" ]; then python3 -m venv .git_hook_venv; fi
.git_hook_venv\Scripts\activate
pip install cryptography ruyaml ruamel.yaml jschon jschon-sort jsonschema click
deactivate
```

**Linux/macOS:**

```bash
if [ "$CRED_MODE" != "enable" ]; then echo "Enable mode not selected — skipping"; exit 0; fi
if [ "$OS_TYPE" = "windows" ]; then echo "Linux/macOS venv — skipping on Windows"; exit 0; fi
if [ ! -d ".git_hook_venv" ]; then python3 -m venv .git_hook_venv; fi
source .git_hook_venv/bin/activate
pip install cryptography ruyaml ruamel.yaml jschon jschon-sort jsonschema click
deactivate
```

### Step 5: Test the Setup

Edit a credentials file and commit it. The pre-commit hook encrypts the file using SOPS before the commit is written.

```bash {"excludeFromRunAll":"true"}
git add "environments/$CLOUD_NAME/$ENV_NAME/Inventory/credentials/$CRED_FILE"
git commit -m "Test SOPS encryption on $CRED_FILE"
```

Verify the commit was created:

```bash {"excludeFromRunAll":"true"}
git log --oneline -1
# Expected: "Test SOPS encryption on <cred-file>"
```

Confirm the committed file contains SOPS-encrypted content (the `sops:` metadata block):

```bash {"excludeFromRunAll":"true"}
if [ "$CRED_MODE" != "enable" ]; then echo "Enable mode not selected — skipping"; exit 0; fi
git show HEAD -- "environments/$CLOUD_NAME/$ENV_NAME/Inventory/credentials/$CRED_FILE" | grep -c "sops:"
# Expected: 1 (the sops: metadata block is present)
```

Confirm your local working-tree copy is still readable (plain text):

```bash {"excludeFromRunAll":"true"}
if [ "$CRED_MODE" != "enable" ]; then echo "Enable mode not selected — skipping"; exit 0; fi
head -5 "environments/$CLOUD_NAME/$ENV_NAME/Inventory/credentials/$CRED_FILE"
# Expected: plain YAML, not encrypted content
```

### Verify Your Encryption is Working

Run after completing all manual steps (Step 3: update `config.yaml` and place key files in `.git/`):

```bash {"excludeFromRunAll":"true"}
if [ "$CRED_MODE" != "enable" ]; then echo "Enable mode not selected — skipping"; exit 0; fi
# Confirm crypt settings in config.yaml
grep -E "crypt" configuration/config.yaml
# Expected: crypt: true and crypt_backend: SOPS

# Confirm the pre-commit hook is present and executable
ls -l .git/hooks/pre-commit
# Expected: -rwxr-xr-x ... .git/hooks/pre-commit

# Confirm key files are in .git/
ls .git/private-age-key.txt .git/age_public_key.txt
# Expected: both files listed without error
```

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

```bash {"excludeFromRunAll":"true"}
git checkout -b backup-fernet-encryption
git commit --allow-empty -m "Backup before SOPS migration"
```

Verify:

```bash {"excludeFromRunAll":"true"}
git log --oneline -2
# Expected: backup branch commit and the previous commit
```

2. **Decrypt all Fernet-encrypted files**:

Confirm the Fernet secret key is present:

```bash {"excludeFromRunAll":"true"}
ls .git/secret_key.txt
# Expected: .git/secret_key.txt listed without error
```

Decrypt each credentials file using the internal script:

```bash
if [ "$CRED_MODE" != "migrate" ]; then echo "Migrate mode not selected — skipping"; exit 0; fi
export SECRET_KEY=$(cat .git/secret_key.txt)
python3 git_hooks/crypt.py decrypt_cred_file \
  -f "environments/$CLOUD_NAME/$ENV_NAME/Inventory/credentials/$CRED_FILE" \
  -s "$SECRET_KEY"
```

Verify the file is now plain text (not encrypted):

```bash
if [ "$CRED_MODE" != "migrate" ]; then echo "Migrate mode not selected — skipping"; exit 0; fi
head -3 "environments/$CLOUD_NAME/$ENV_NAME/Inventory/credentials/$CRED_FILE"
# Expected: plain YAML content, not a Fernet-encrypted string
```

### Step 2: Set Up SOPS

1. **Follow the SOPS setup steps** described in the [How to enable Credential encryption](#how-to-enable-credential-encryption) section above
2. **Generate age keys** and store them in CI/CD variables
3. **Install SOPS tools** and dependencies

### Step 3: Update Configuration

1. **Change encryption backend** in `/configuration/config.yaml`:

```yaml {"excludeFromRunAll":"true"}
crypt: true  # Re-enable encryption
crypt_backend: SOPS  # Changed from Fernet
```

2. **Remove Fernet key file**:

```bash
if [ "$CRED_MODE" != "migrate" ]; then echo "Migrate mode not selected — skipping"; exit 0; fi
rm .git/secret_key.txt
```

3. **Add SOPS age keys**:

   - Place `private-age-key.txt` in `.git/` directory
   - Place `age_public_key.txt` in `.git/` directory

### Step 4: Re-encrypt Files

1. **Test the new setup** with a single file first:

```bash {"excludeFromRunAll":"true"}
git add "environments/$CLOUD_NAME/$ENV_NAME/Inventory/credentials/$CRED_FILE"
git commit -m "Test SOPS encryption on $CRED_FILE"
```

Confirm the committed file contains SOPS-encrypted content:

```bash {"excludeFromRunAll":"true"}
git show HEAD -- "environments/$CLOUD_NAME/$ENV_NAME/Inventory/credentials/$CRED_FILE" | grep -c "sops:"
# Expected: 1
```

2. **Re-encrypt all credential files**:

```bash {"excludeFromRunAll":"true"}
git add "environments/$CLOUD_NAME/$ENV_NAME/Inventory/credentials/"
git commit -m "Migrate all credentials to SOPS encryption"
```

Verify:

```bash {"excludeFromRunAll":"true"}
git log --oneline -1
# Expected: "Migrate all credentials to SOPS encryption"
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

```bash {"excludeFromRunAll":"true"}
git branch -d backup-fernet-encryption
```
