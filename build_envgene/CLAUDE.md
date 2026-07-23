# build_envgene — EnvGene Docker Image Build

Docker image `qubership-envgene` (`build_envgene/build/Dockerfile`). `COPY scripts/ /module/scripts/` ships the whole single-job pipeline tree (see `scripts/CLAUDE.md`) into the image. `WORKDIR /module/scripts` is the container's entry point, running `pipeline/orchestrator.py`.

This directory only holds Docker build context now (`build/Dockerfile`, `build/requirements.txt`, `build/pip.conf`, `build/constraint.txt`, `build/sources.list`) and the `workflows/` template. The Python scripts that used to live at `build_envgene/scripts/` moved to `scripts/`: `git_commit.py`/`minimize_cred_diffs.py` are now under `scripts/git_commit/`, `report.py` directly under `scripts/` — see `scripts/CLAUDE.md` for their responsibilities and `scripts/tests/git_commit/` for their tests.

## Credential Diff Minimization (`scripts/git_commit/minimize_cred_diffs.py`)

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

The actual Git plumbing (`GitRepoManager`, `GitContext`, `GitLabClient`, sparse-checkout path list) lives in `modules/envgene/envgenehelper/git_helper.py` and `repo_paths.py`, not here.
