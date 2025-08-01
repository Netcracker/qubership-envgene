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

### 2. Install dependencies

```bash
pip install -r requirements.txt
```
And also install `envgenehelper`

### 3. Provide required keys

Place the following files (if applicable):

- `./.git/SECRET_KEY.txt` — your Fernet secret key (used for decryption)
- `./.git/PUBLIC_AGE_KEYS.txt` — age public keys (used for encryption)

Or pass key files manually with `-f` option in CLI.

> 🔐 You can generate a Fernet key using:
> ```bash
> python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
> ```

### 4. Install the pre-commit hook

```bash
cp script.py .git/hooks/pre-commit
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
python script.py encrypt -f ./path/to/public-keys.txt
```

If `-f` is omitted, it uses `.git/PUBLIC_AGE_KEYS.txt`.

### 🔓 Manual Decryption

```bash
python script.py decrypt -f ./path/to/private-key.txt
```

If `-f` is omitted, it uses:

- `.git/SECRET_KEY.txt` (Fernet key for decryption)
- Assumes env vars or placeholders are already set

---

## 🧠 Environment Variables Used

| Variable                        | Purpose                                 |
|--------------------------------|-----------------------------------------|
| `ENVGENE_AGE_PRIVATE_KEY`      | Private key content for age            |
| `ENVGENE_AGE_PUBLIC_KEY`       | Placeholder to activate logic          |
| `PUBLIC_AGE_KEYS`              | Public age keys content                |
| `SECRET_KEY`                   | Symmetric key for Fernet encryption    |

---

## 🌐 Cross-platform

- Works on Linux, macOS, Windows
- Hook script auto-detects the OS and selects appropriate Python binary:
  - `venv/bin/python` for Unix
  - `venv/Scripts/python.exe` for Windows
  - Falls back to `python3` or `python` if no venv

---

## 🧪 Troubleshooting

Run the pre-commit hook manually to debug:

```bash
.git/hooks/pre-commit
```

Make sure:
- Your keys are placed correctly
- `envgenehelper` is installed
- Python executable is found