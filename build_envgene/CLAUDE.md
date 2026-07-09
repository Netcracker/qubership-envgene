# build_envgene — EnvGene Pipeline Jobs Docker Image

Docker image `qubership-envgene` (`build_envgene/build/Dockerfile`). In this branch it packages **both** this directory's scripts and the whole `scripts/` tree (single-job pipeline, see `scripts/CLAUDE.md`) — `COPY scripts/ /module/scripts/` then `COPY build_envgene/scripts/ /module/scripts/`, so `/module/scripts/` is their union. `WORKDIR /module/scripts` is the container's entry point, running `pipeline/orchestrator.py`.

## Scripts (`scripts/`)

| File | Responsibility |
|------|---------------|
| `minimize_cred_diffs.py` | Diffs HEAD vs working tree, re-encrypts changed cred files using HEAD version as `old_file_path` for `minimize_diff=True`; caches results by `(head_blob_sha, source_sha)`; called from `git_commit.py` before staging |
| `git_commit.py` | `git_commit()`: configures `GitRepoManager` (from `envgenehelper.git_helper`), stages changes, creates a detached commit, then `retry_cherry_pick_and_push` — fetches latest ref, cherry-picks the detached commit, pushes, retrying via `envgenehelper.retry` on failure. Replaces the old `git_commit.sh` (deleted) |
| `report.py` | Generates pipeline summary reports |

The actual Git plumbing (`GitRepoManager`, `GitContext`, `GitLabClient`, sparse-checkout path list) lives in `python/envgene/envgenehelper/git_helper.py` and `repo_paths.py`, not here.

## Credential Diff Minimization (`minimize_cred_diffs.py`)

**Purpose:** Reduce noisy Git diffs in encrypted credential files. Each Fernet encryption generates a new random token, so re-encrypting an unchanged value produces a different ciphertext. By reusing old tokens when plaintext values haven't changed, the diff only shows lines that actually changed.

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
