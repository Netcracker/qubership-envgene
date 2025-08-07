# 🔐 Pre-commit Secrets Encryption Hook

This project provides a Git pre-commit hook and CLI tool for encrypting/decrypting sensitive credentials using `envgenehelper`module.

- ✅ Pre-commit hook: **encrypts** credentials automatically before each commit.
- ✅ CLI interface: allows **manual encrypt/decrypt** operations.

---

## 📦 Requirements

- Python 3.8+
- Git installed
- Git Bash
- Virtual environment (`venv`) recommended
- `envgenehelper` and its dependencies

---

## 🛠 Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
```

### 2. Install SOPS 

#### For UNIX

```bash
curl --retry 3 --retry-connrefused --retry-delay 5 -LO https://github.com/mozilla/sops/releases/download/v3.9.0/sops-v3.9.0.linux.amd64
chmod +x sops-v3.9.0.linux.amd64 
mv sops-v3.9.0.linux.amd64 /usr/local/bin/sops 
```
#### For Windows+venv

Put sops.exe  in `venv/Scripts`
### 2. Install python dependencies

```bash
pip install -r requirements.txt
```
And also install `envgenehelper` python lib

```bash
pip install ./qubership-envgene/python/envgene ./qubership-envgene/python/jschon-sort
```

### 3. Provide required keys

Place the following files (if applicable):

- `./.git/SECRET_KEY.txt` — your Fernet secret key (used for decryption)
- `./.git/PUBLIC_AGE_KEYS.txt` — age public keys (used for encryption)

Or pass key files manually with `-f` option in CLI.

### 4. Install the pre-commit hook

```bash
cp pre-commit.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

---

## 🚀 Usage

### ✅ Git Hook (Encrypt on Commit)

Whenever you run `git commit`, the hook will:

- Encrypt all relevant secret files using `envgenehelper`
- Automatically add encrypted files to the commit
- Use `venv` if available, or fallback to system Python

🔸 **Note:** The hook **does not decrypt** — only encryption is supported in pre-commit.

### 🔐 Manual Encryption

```bash
python pre-commit.py encrypt -f ./path/to/public-keys.txt
```

If `-f` is omitted, it uses `.git/PUBLIC_AGE_KEYS.txt`.

### 🔓 Manual Decryption

```bash
python pre-commit.py decrypt -f ./path/to/private-key.txt
```

If `-f` is omitted, it uses:

- `.git/SECRET_KEY.txt` (Fernet key for decryption)
- Assumes env vars or placeholders are already set

Which type of decryption/encryption will be used depends on `/configuration/config.yml` content
---

## 🧠 Environment Variables Used

| Variable                        | Purpose                                 |
|--------------------------------|-----------------------------------------|
| `ENVGENE_AGE_PRIVATE_KEY`      | Private key content for age            |
| `ENVGENE_AGE_PUBLIC_KEY`       | Placeholder to activate logic          |
| `PUBLIC_AGE_KEYS`              | Public age keys content                |
| `SECRET_KEY`                   | Symmetric key for Fernet encryption    |

---
