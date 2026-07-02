# build_envgene — EnvGene Pipeline Jobs Docker Image

Docker image `qubership-envgene`. Runs all core pipeline jobs except Effective Set generation: env build, git commit, credential diff minimization, and reporting.

## Scripts (`scripts/`)

| File | Responsibility |
|------|---------------|
| `minimize_cred_diffs.py` | Git pre-commit hook: diffs HEAD vs working tree, re-encrypts changed cred files using HEAD version as `old_file_path` for `minimize_diff=True`; caches results by `(head_blob_sha, source_sha)` |
| `git_commit.sh` | Stages changes, creates a git commit in the instance repository after pipeline jobs complete; used by the `git_commit` pipeline job |
| `report.py` | Generates pipeline summary reports |

## Credential Diff Minimization (`minimize_cred_diffs.py`)

**Purpose:** Reduce noisy git diffs in encrypted credential files. Each Fernet encryption generates a new random token, so re-encrypting an unchanged value produces a different ciphertext. By reusing old tokens when plaintext values haven't changed, the diff only shows lines that actually changed.

**Algorithm:**
1. `git diff --name-only HEAD` → list of changed files
2. Filter to credential files via `is_cred_file()`
3. For each changed cred file:
   - Read HEAD blob content
   - Decrypt working-tree version in-place
   - Re-encrypt with `minimize_diff=True, old_file_path=<HEAD-temp-file>`
4. Cache result keyed by `(head_blob_sha, source_sha)` in `MINIMIZE_CRED_DIFF_CACHE_DIR`

**Skipped when:**
- `get_crypt()` returns False (encryption disabled in config.yml)
- File is new (not in HEAD) — no old tokens to reuse
- Old file is not encrypted

## Tests

```bash
cd build_envgene/scripts
python -m pytest
```
Test file: `test_minimize_cred_diffs.py`.
