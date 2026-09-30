# Executable Analysis: How-To Guides — Consolidated (All 6 Guides)

This document records the analysis and decisions for making the following six EnvGene how-to guides executable —
runnable by a human from the terminal, by VS Code, by a GitLab CI pipeline, and by an AI agent.

**Guides covered:**

1. `app-reg-defs-add-without-template.md`
2. `configure-resource-profiles.md`
3. `configure-system-certificates.md`
4. `credential-encryption.md`
5. `dot-notated-parameter-migration.md`
6. `configure-cloud-artifact-registries.md`

**Execution tooling:** [runme](https://runme.dev/) via `npx runme run` — no installation required.

**Brief source:** `executable_howto.txt` — goals, in-scope questions, and five deliverables.

**How to run any guide:** See [How to run guides with runme](how-to-run-guides-with-runme.md).

---

## Answers to Core Questions

These answer the questions from `executable_howto.txt` for all six guides.

### Q1 — What does the approach require from the guide text so it can be run and verified?

Six requirements — see [Part 5 — Conclusions](#part-5--conclusions) for the full list with rationale.
A seventh requirement emerged from this batch: **conditional-flow guards must use `if/fi` form**, not `&&` short-circuit patterns.

### Q2 — Does every step need a checkable result, or is "ran without error" enough?

Exit code 0 is never sufficient on its own. What counts as adequate verification depends on the command type:

| Command type | Why exit code 0 is not enough | Minimum check used in these guides |
|---|---|---|
| `:?` validation | Exits 0 when all vars are set — that is the success case | `echo "Inputs OK"` confirms the cell completed |
| `mkdir -p` | Exits 0 even if the path already existed as a file | `ls -d <path>` confirms it is a directory |
| `cat > file <<EOF` heredoc | Exits 0 even if `$VAR` was unset and wrote an empty string | `cat` the file; confirm values are substituted, not empty or literal `${VAR}` |
| `git add / commit` | Exits 0 when "nothing to commit" — no commit was created | `git log --oneline -1` confirms commit with expected message |
| `git push` | Exits 0 but remote may reject (auth error, protected branch) | Auth errors surface as non-zero; absence of error is the only local check |
| `git pull` | Exits 0 even if no new commits were pulled | `ls` of the expected output directory confirms the pipeline wrote files |
| `openssl x509` | Reads only the first cert in a chain file; later certs may be invalid | `openssl crl2pkcs7 \| pkcs7 -print_certs -noout` for multi-cert files |
| `python3 yaml.safe_load` | Exits 0 if `SEARCH_DIR` contains no YAML files — silent false positive | File count in scan output must be > 0 before trusting "all files valid" |
| `grep` re-scan for dot-notation | Exits **1** when no matches found — this is the success case | `\|\| echo "OK"` pattern; exit 1 means "no dot keys found" |
| `git show ... \| grep sops:` | Exits 0 just means SOPS metadata present | Count (`-c`) must be `1`, not just non-zero |
| PROVIDER-conditional file creation | Cell exits 0 on skip — no file is created | Verify cell also guards on PROVIDER; `cat` confirms values substituted |

**Rule across all six guides:** Every step that writes a file, modifies a git tree, or interacts with a remote
system needs a result check, not just an exit-code check. Commands that are purely read-only prerequisite checks
(tool version, `ls`) need only exit code plus expected output string.

---

### Q3 — Which requirements are equally useful for human, CI, and AI agent?

| Requirement | Human | CI | AI agent |
|---|---|---|---|
| All actions in `bash` blocks | Helpful (copy-paste) | **Required** | **Required** |
| `Required Inputs` table + `KEY=value` template | **Required** (no guessing format or valid values) | **Required** | **Required** |
| `:?` validation as first runnable cell | Very helpful (catches mistakes early) | **Required** (job fails with named error) | **Required** (agent gets clear stop message) |
| `--env-file` / `source` input pattern | Helpful (no editing the guide) | **Required** (CI vars passed cleanly) | **Required** (agent writes the file from conversation context) |
| Manual-step callouts (`> **Manual step...**`) | Informative | **Required** (skip signal — blockquotes are not bash cells) | **Required** (agent stop signal) |
| Post-step verification commands | Reassuring | **Required** | **Required** |
| `# Expected:` comments in verification cells | Very helpful | Useful for log inspection | **Required** (agent compares actual output to expected) |
| Real example content (no `<placeholders>`) | **Required** (cannot run invalid YAML/shell) | **Required** | **Required** |
| `if/fi` guard form for conditional cells | Transparent | **Required** (&&-form exits 1 on skip, causing job failure) | **Required** |
| Conditional validation (`:?` only for active PROVIDER) | Helpful (no spurious errors) | **Required** | **Required** |

All requirements are equally required for CI and AI agent. For humans, the `Required Inputs` table and real
example content are also strictly required — a human cannot run a command with a shell-invalid placeholder any
more than a CI runner can.

---

## Part 1 — Execution Approach

### How to run a guide

```bash
(set -a; source my-inputs.txt; npx runme run --all --filename docs/how-to/<guide>.md)
```

`npx runme` requires only Node.js (v16+). No separate runme installation is needed.

### How to provide input values

Each guide has a **Required Inputs** section with:

- A table of variables (name, required/optional, example, description)
- A plain `KEY=value` template to copy

Create a file from the template, fill in real values, source it before running. The filename does not matter.

```
# my-inputs.txt
APP_NAME=payment-service
REGISTRY_NAME=nexus-prod
```

```bash
(set -a; source my-inputs.txt; npx runme run --all --filename app-reg-defs-add-without-template.md)
```

This single pattern works across all four execution contexts — see the table below.

### Execution contexts

| Context | How inputs are passed | Notes |
|---|---|---|
| **CLI** | `set -a; source inputs.txt` before run | `set -a` exports all sourced vars into the environment |
| **VS Code** | `export` vars in integrated terminal then click **Run** per cell, or source in terminal then run with `--all` | Runme extension renders bash cells with ▶ buttons |
| **GitLab pipeline** | CI/CD variables set at project level or in `.gitlab-ci.yml` `variables:` block | Pipeline env vars are already in scope when the job starts |
| **AI agent** | Agent reads the Required Inputs table, collects values from conversation, writes the input file, runs guide | `# Expected:` comments in verification cells tell the agent what output to check |

### Why `if/fi` guards instead of `&&` short-circuit

`[ "$VAR" != "value" ] && { echo "skipping"; exit 0; }` exits with the test's exit code (1) when the condition
is false — i.e., when the cell *should* run. runme and CI treat exit code 1 as a cell failure. All guards in
these guides use:

```bash
if [ "$VAR" != "value" ]; then echo "skipping"; exit 0; fi
```

This form is always a conditional construct: the `if/fi` wrapper never propagates the test's exit code.

### Why `:?` validation instead of `${VAR:-default}`

`${VAR:-default}` silently runs with example values if the user forgets to source an inputs file. This produces
wrong files with no error. `:?` validation fails immediately with a readable message:

```
VAR is required — see Required Inputs section
```

Optional variables that have a safe default use `${VAR:-default}` because the default is always correct.

### Why conditional validation for multi-provider guides

`configure-cloud-artifact-registries.md` requires different variables depending on PROVIDER. Validating all
15 variables unconditionally would force every user to supply GCP variables even for `PROVIDER=aws`. The
validate-inputs cell uses `if [ "$PROVIDER" = "aws" ] || [ "$PROVIDER" = "both" ]; then :?...; fi` blocks so
only the active provider's variables are checked.

---

## Part 2 — Per-Guide Analysis

### app-reg-defs-add-without-template.md

**What was made executable:**

| Step | Was | Became |
|---|---|---|
| Create AppDef/RegDef file | Prose + static YAML example | `mkdir -p` + `cat >` heredoc with `$VAR` substitution |
| Commit and push | Prose | `git add / commit / push` bash block |
| Trigger pipeline | Prose | Manual-step callout (blockquote) |
| Verify output | Prose | `git pull` + `ls` + `cat` bash blocks |

**Required inputs:** `APP_NAME`, `REGISTRY_NAME`

**What remains manual:** Pipeline trigger (GitLab UI or API). Verification of pipeline-internal processing
(`app_reg_def_process` job output) is visible only in GitLab job logs.

**Verification map:**

| Step | Verification command | What it confirms |
|---|---|---|
| Create AppDef file | `cat configuration/appdefs/$APP_NAME.yml` | Values substituted, not literal `${APP_NAME}` strings |
| Commit | `git log --oneline -1` | Commit message present |
| Post-pipeline | `ls appdefs/` + `cat appdefs/$APP_NAME.yml` | Output file written by pipeline |

**What remains unverifiable:**

| Step | Reason |
|---|---|
| `app_reg_def_process` job execution | Pipeline runs inside GitLab CI; job output visible only in job logs, not locally |
| Override merge correctness | Whether EnvGene correctly merged the override into effective definitions requires inspecting `appdefs/` after pipeline — the post-pipeline `cat` check covers file presence, not semantic correctness |

---

### configure-resource-profiles.md

**What was made executable:**

| Step | Was | Became |
|---|---|---|
| Option 1 git commit/push | `bash` block (already present) | Added `git log` verification + manual publish callout |
| Option 2 git commit/push | `bash` block (already present) | Added `git log` verification + pipeline trigger callout |
| Scope table | `<angle-bracket>` placeholders | `$CLUSTER_NAME` / `$ENV_NAME` references |
| Verification section | `text` blocks + prose | `git pull` + `ls` + `cat` + `find` bash blocks |
| Option 2 commit: env_definition.yml staging | Always staged unconditionally | `git diff --ignore-all-space` check — only stages if Step 3 was completed |

**Required inputs:** `PROFILE_NAME` (Option 1) or `CLUSTER_NAME`, `ENV_NAME`, `PROFILE_OVERRIDE_NAME` (Option 2)

**What remains manual:** Template publish step (Option 1); pipeline trigger (Option 2); `env_definition.yml`
editing (Step 3); merge result inspection (generated profile must be read manually to verify business logic).

**Verification map:**

| Step | Verification command | What it confirms |
|---|---|---|
| Commit | `git log --oneline -1` | Commit message present |
| Post-pipeline (Option 2) | `ls environments/$CLUSTER_NAME/$ENV_NAME/Profiles/` | Profile file written |
| Inspect merged profile | `cat environments/$CLUSTER_NAME/$ENV_NAME/Profiles/$PROFILE_OVERRIDE_NAME.yml` | Merged values present |

**What remains unverifiable:**

| Step | Reason |
|---|---|
| Template publish success (Option 1) | Team-specific publish process; no local CLI equivalent |
| Profile merge business logic | `cat` of the generated profile confirms values are present but not that the merge is semantically correct for the application |
| Instance pipeline trigger outcome | Pipeline runs inside GitLab CI; success visible only in job logs |

---

### configure-system-certificates.md

**What was made executable:**

| Step | Was | Became |
|---|---|---|
| Validate inputs | None | `:?` validation for `CERT`, `HOST`; `PORT` defaults to `443` |
| Inspect cert | Prose | `openssl x509` bash block |
| Create certs directory | Prose | `mkdir -p configuration/certs` bash block |
| Place cert in repo | Prose | Manual-step callout (file contains secrets/PEM content) |
| Commit and push | Prose | Excluded — commit is after the manual placement step |
| Verify with live host | Prose | `openssl s_client` bash block (excluded — requires live TLS host) |

**Required inputs:** `CERT` (path to PEM cert file), `HOST` (TLS hostname), `PORT` (optional, default `443`)

**What remains manual:** Browser-based certificate export; placing the cert into `configuration/certs/`; GitLab pipeline trigger.

**Verification map:**

| Step | Verification command | What it confirms |
|---|---|---|
| Cert validity | `openssl x509 -in "$CERT" -noout -subject -issuer -dates` | PEM-encoded, includes subject/issuer/dates |
| Directory created | `ls -d configuration/certs/` | Directory exists |
| TLS connection | `openssl s_client -connect $HOST:$PORT -CAfile "$CERT"` (excluded) | Server presents cert chaining to `$CERT` |

**What remains unverifiable:**

| Step | Reason |
|---|---|
| EnvGene trust store rebuild | Happens inside the GitLab CI pipeline; not observable locally |
| Browser-exported cert validity | `openssl x509` confirms PEM encoding but cannot confirm the cert was exported from the correct service or trust hierarchy |
| Pipeline TLS connection success | Whether EnvGene successfully connects to `$HOST` using the cert is visible only in pipeline job logs |

---

### credential-encryption.md

**What was made executable:**

| Step | Was | Became |
|---|---|---|
| Install SOPS CLI | `bash` block (already present) | No change needed |
| Generate age keys | `bash` block (already present) | Made idempotent (skips if `private-age-key.txt` exists) |
| Store keys in CI/CD | Prose bullet list | Manual-step callout |
| Configure config.yaml | Manual prose | Automated: checks both `.yaml` and `.yml`; updates `crypt:` and `crypt_backend:` or creates file |
| Place key files in `.git/` | Manual prose | Automated: `cp private-age-key.txt .git/` + `cp age_public_key.txt .git/` |
| Install pre-commit hook | `bash` block | No change needed |
| Set up Python venv | `bash` block | Split into Windows/Linux cells with OS_TYPE guard; made idempotent (`if [ ! -d .git_hook_venv ]`) |
| Test the setup | Prose | `git add / commit` + `git show \| grep sops:` + `head` verification |
| Verify encryption working | Empty section (bug) | Three bash verification checks |
| CRED_MODE flow selection | None | `CRED_MODE=enable/migrate` variable; all cells guarded with `if/fi` mode check |
| Fernet migration — decrypt | `<angle-bracket>` placeholders | `$CLOUD_NAME`, `$ENV_NAME`, `$CRED_FILE` references |
| Fernet migration — re-encrypt | `<angle-bracket>` placeholders | `$VAR` references + verification |

**Required inputs:** `CRED_MODE` (`enable` or `migrate`), `CLOUD_NAME`, `ENV_NAME`, `CRED_FILE`, `OS_TYPE` (optional, default `linux`)

**What remains manual:** Adding CI/CD variables (`PUBLIC_AGE_KEYS`, `ENVGENE_AGE_PRIVATE_KEY`) via GitLab UI;
verifying pipeline decryption (visible only in CI job logs).

**Verification map:**

| Step | Verification command | What it confirms |
|---|---|---|
| Key generation | `ls .git/private-age-key.txt .git/age_public_key.txt` | Key files present |
| Config update | `grep -E "^crypt" $CONFIG_FILE` | `crypt: true` and `crypt_backend: SOPS` present |
| Pre-commit hook | `ls -l .git/hooks/pre-commit` | Hook is executable |
| Encryption test | `git show HEAD -- <cred-file> \| grep -c "sops:"` | SOPS metadata present in committed file |
| Local file readable | `head -5 <cred-file>` | Local copy is plain YAML |
| Fernet decrypt | `head -3 <cred-file>` | File is plain text, not encrypted |

**What remains unverifiable:**

| Step | Reason |
|---|---|
| GitLab CI/CD decryption success | Pipeline SOPS decryption runs inside CI; visible only in job logs |
| `PUBLIC_AGE_KEYS` / `ENVGENE_AGE_PRIVATE_KEY` variable correctness | Values entered manually in GitLab UI; no local check can confirm they are correct until the first pipeline run attempts decryption |

---

### dot-notated-parameter-migration.md

**What was made executable:**

| Step | Was | Became |
|---|---|---|
| Find dot-notation params | "Identify parameters" (prose) | `grep -rn` scanner bash block |
| Rename keys | "Convert each key" (prose) | Manual-step callout (inherently manual) |
| Validate YAML | Not present | `python3 yaml.safe_load` over all files |
| Confirm no dots remain | Not present | `grep` re-scan with `\|\| echo "OK"` pass/fail |
| Commit | Not present | `git add / commit / push` + `git log` verification |
| Example YAML blocks | Runnable bare `yaml` blocks | Excluded with `{"excludeFromRunAll":true}` |

**Required inputs:** `SEARCH_DIR` (optional, default `environments`)

**What remains manual:** Renaming dot-notation YAML keys — this is a text editing operation with no CLI
equivalent that is safe to run non-interactively.

**Verification map:**

| Step | Verification command | What it confirms |
|---|---|---|
| Find dots | `grep -rn ...` | Identifies files needing migration |
| Post-edit YAML check | `python3 yaml.safe_load` over all files | No YAML parse errors introduced |
| Post-edit dot check | `grep -rn ...` re-scan | No dot-notation keys remain |
| Commit | `git log --oneline -1` | Commit message present |

**What remains unverifiable:**

| Step | Reason |
|---|---|
| Semantic correctness of renamed keys | YAML validity is confirmed by `python3 yaml.safe_load`; whether the renamed key has the correct meaning in application context requires human review |
| Completeness of migration scope | The `grep` re-scan covers `$SEARCH_DIR` only; YAML files outside that directory are not checked |

---

### configure-cloud-artifact-registries.md

**What was made executable:**

| Step | Was | Became |
|---|---|---|
| Input validation | None (pure reference doc) | Full `Required Inputs` section; 15-variable validate-inputs cell with PROVIDER-conditional `:?` checks |
| AWS credential entry | Prose + static YAML | Manual-step callout (contains secrets) + excluded `yaml` example block |
| AWS registry definition file | Prose + static YAML | `cat >` heredoc bash cell with `$VAR` substitution; skips when `PROVIDER=gcp\|both` |
| GCP credential entry | Prose + static YAML | Manual-step callout (contains secrets) + excluded `yaml` example block |
| GCP registry definition file | Prose + static YAML | `cat >` heredoc bash cell with `$VAR` substitution; skips when `PROVIDER=aws\|both` |
| Both providers simultaneously | Not present | Parallel bash cell using `create_aws & create_gcp & wait`; runs only when `PROVIDER=both` |
| Commit and push | Not present | `git add / commit / push` + `git log` verification section |
| Pipeline trigger | Not present | Manual-step callout |

**Conditional flows:**

| PROVIDER value | AWS creation cell | GCP creation cell | Parallel cell |
|---|---|---|---|
| `aws` | Runs | Skips | Skips |
| `gcp` | Skips | Runs | Skips |
| `both` | Skips (parallel handles it) | Skips (parallel handles it) | Runs |

**Required inputs:**
- Always: `PROVIDER`
- When `PROVIDER=aws` or `both`: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_DOMAIN`, `AWS_REPO_URL`; optional with defaults: `AWS_CRED_KEY`, `AWS_REGDEF_NAME`
- When `PROVIDER=gcp` or `both`: `GCP_SA_KEY_FILE` (must exist on disk), `GCP_REGION`, `GCP_PROJECT_ID`, `GCP_MAVEN_REPO`; optional with defaults: `GCP_CRED_KEY`, `GCP_REGDEF_NAME`

**What remains manual:** Editing `configuration/credentials/credentials.yml` to add the credential entry (Step 1 for each provider) — secrets must not be automated; encryption of the credential entry (see `credential-encryption.md`); pipeline trigger after commit.

**Verification map:**

| Step | Verification command | What it confirms |
|---|---|---|
| AWS registry definition | `cat configuration/registry_definitions/$AWS_REGDEF_NAME.yaml` (PROVIDER guard) | Values substituted, not literal `$VAR` strings |
| GCP registry definition | `cat configuration/registry_definitions/$GCP_REGDEF_NAME.yaml` (PROVIDER guard) | Values substituted |
| Parallel creation | `ls configuration/registry_definitions/` after `wait` | Both files listed |
| Commit | `git log --oneline -1` | Commit message present |

**What remains unverifiable:**

| Step | Reason |
|---|---|
| `credentials.yml` correctness | File contains secrets — not readable post-encryption; format is verified only by EnvGene at runtime |
| EnvGene authentication success | Whether the registry definition + credential actually authenticate to AWS CodeArtifact or GCP Artifact Registry is visible only in the pipeline job that attempts a Maven download |
| AWS CodeArtifact end-to-end | AWS support noted as untested in the guide — `authMethod: secret` is implemented but not validated against a live CodeArtifact repository |

**Key design decisions:**

1. **Individual cells skip for `PROVIDER=both`** — avoids double-creation when the parallel section already creates both files. Guard: `if [ "$PROVIDER" = "gcp" ] || [ "$PROVIDER" = "both" ]; then exit 0; fi`.
2. **PROVIDER-conditional validation** — `:?` checks for AWS vars run only inside `if [ "$PROVIDER" = "aws" ] || [ "$PROVIDER" = "both" ]` block; likewise for GCP. This prevents spurious failures for unused providers.
3. **`GCP_SA_KEY_FILE` file-existence check** — `[ -f "$GCP_SA_KEY_FILE" ] || { echo "ERROR: ..."; exit 1; }` in validate-inputs catches a missing file before any cell attempts to read it.
4. **Parallel execution** — `create_aws & create_gcp & wait` in a single bash cell; background subshells write independent files with no shared state, so there are no race conditions.

---

## Part 3 — Combined Required Inputs

### Local prerequisites (no external system needed)

| Prerequisite | Guides | Notes |
|---|---|---|
| Node.js v16+ (for `npx runme`) | all six | `node --version` to confirm |
| Git on PATH | all six | `git --version` to confirm |
| OpenSSL on PATH | configure-system-certificates | `openssl version` to confirm |
| cURL on PATH | configure-system-certificates | `curl --version` to confirm |
| Python 3 on PATH | dot-notated-parameter-migration | `python3 --version` to confirm |
| SOPS CLI on PATH | credential-encryption | Installed in Step 1 of the guide |
| age / age-keygen on PATH | credential-encryption | Installed in Step 1 of the guide |

### Remote fixtures required

| Fixture | Guides | Notes |
|---|---|---|
| Instance repository cloned locally | all six | Write access required |
| GitLab instance with accessible test group | app-reg-defs, configure-resource-profiles, credential-encryption, configure-cloud-artifact-registries | Group URL is base of repo URLs |
| `GITLAB_TOKEN` with write access | app-reg-defs, configure-resource-profiles, credential-encryption, configure-cloud-artifact-registries | Do not commit to version control |
| Reachable TLS host (`$HOST:$PORT`) with private CA | configure-system-certificates | Must present a cert signed by a non-public CA |
| Valid CA certificate in PEM format | configure-system-certificates | Self-signed test CA is sufficient |
| Template repository with Cloud/Namespace templates | configure-resource-profiles | Required for Option 1 |
| Pre-existing cluster directory in instance repo | configure-resource-profiles | `$CLUSTER_NAME` must match an existing directory |
| AWS IAM credentials with CodeArtifact permissions | configure-cloud-artifact-registries (aws/both) | `codeartifact:GetAuthorizationToken`, `codeartifact:ReadFromRepository`, `sts:GetServiceBearerToken` |
| GCP service account JSON key file on local disk | configure-cloud-artifact-registries (gcp/both) | `roles/artifactregistry.reader` on target repository |

### Required test files for CI execution

| File | Guide | Description | Synthetic? |
|---|---|---|---|
| `configuration/certs/ca-chain.pem` | configure-system-certificates | CA certificate in PEM format | Yes — any self-signed test CA cert |
| `server-cert.pem` | configure-system-certificates | Server certificate for chain-build example | Yes — any valid PEM cert |
| `.git/private-age-key.txt` | credential-encryption | age private key | Yes — generated by `age-keygen` in the guide itself; not committed |
| `.git/age_public_key.txt` | credential-encryption | age public key | Yes — extracted from private key in the guide itself; not committed |
| `environments/$CLOUD_NAME/$ENV_NAME/Inventory/credentials/$CRED_FILE` | credential-encryption | Plaintext credentials YAML to encrypt | Yes — any valid Credential YAML with at least one `password:` field |
| `git_hooks/pre-commit` | credential-encryption | Pre-commit hook script | No — must come from the actual instance repository |
| `environments/$CLUSTER_NAME/` directory | configure-resource-profiles | Pre-initialized cluster directory | No — must match EnvGene's required `environments/` layout |
| `environments/$CLUSTER_NAME/$ENV_NAME/Inventory/env_definition.yml` | configure-resource-profiles | Environment inventory file | No — must match EnvGene's required schema |
| `templates/` directory | configure-resource-profiles (Option 1) | Template repository with Cloud/Namespace templates | No — must be a real EnvGene template repository |
| `$SEARCH_DIR/**/*.yml` with dot-notation keys | dot-notated-parameter-migration | YAML files containing `a.b: value` keys to migrate | Yes — any YAML with dot-notation parameter keys |
| `configuration/` directory with `appdefs/` and `regdefs/` | app-reg-defs | Output directories written by the EnvGene pipeline | No — created by EnvGene; must be present before the post-pipeline verify step |
| `configuration/credentials/credentials.yml` | configure-cloud-artifact-registries | Credential file with AWS or GCP entry (manually edited) | No — contains secrets; must be provided by user |
| `/path/to/sa-key.json` | configure-cloud-artifact-registries (gcp/both) | GCP service account JSON key file | No — downloaded from GCP IAM console |

**Notes:**
- Secret files (`private-age-key.txt`, `GITLAB_TOKEN`, GCP SA key) must never be committed — pass via CI/CD protected variables only.
- The `configuration/appdefs/` and `configuration/regdefs/` input directories are created by the guide (`mkdir -p`). The output `appdefs/` and `regdefs/` directories are written by the pipeline and require a real EnvGene run.
- `configuration/registry_definitions/` is created by the guide (`mkdir -p`); no pre-existing structure required.

### Permanently manual (no fixture can replace)

| Step | Guide | Reason |
|---|---|---|
| `app_reg_def_process` pipeline trigger | app-reg-defs | GitLab CI; not a local shell operation |
| Template publish | configure-resource-profiles | Team-specific publish process |
| Instance pipeline trigger | configure-resource-profiles | GitLab CI |
| Browser certificate export | configure-system-certificates | GUI-only, no CLI equivalent |
| Pipeline trust-store rebuild | configure-system-certificates | GitLab CI |
| GitLab CI/CD variable configuration | credential-encryption | Project Settings UI; token shown only at issuance |
| Dot-notation key renaming | dot-notated-parameter-migration | Text edit; no safe non-interactive equivalent |
| AWS/GCP credential entry in `credentials.yml` | configure-cloud-artifact-registries | Contains secrets; must be edited and encrypted manually |
| Instance pipeline trigger (registry pickup) | configure-cloud-artifact-registries | GitLab CI |

---

## Part 4 — Acceptance Criteria Per Guide

### app-reg-defs-add-without-template.md

1. `(set -a; source inputs.txt; npx runme run --all --filename app-reg-defs-add-without-template.md)` exits 0.
2. The validate-inputs cell fails with a clear message when `APP_NAME` or `REGISTRY_NAME` is not set.
3. After file creation, `cat configuration/appdefs/$APP_NAME.yml` shows actual values (not `${APP_NAME}` literals).
4. `git log --oneline -1` shows the expected commit message after push.

### configure-resource-profiles.md

1. The validate-inputs cell fails with a clear message for each missing variable.
2. `git log --oneline -1` shows the expected message after the Option 2 commit.
3. After the pipeline runs, `ls environments/$CLUSTER_NAME/$ENV_NAME/Profiles/` shows the profile file.

### configure-system-certificates.md

1. The validate-inputs cell fails if `CERT` or `HOST` is not set; `PORT` defaults to `443`.
2. `openssl x509 -in "$CERT" -noout -subject -issuer -dates` exits 0 with subject/issuer/date output.
3. `git log --oneline -1` shows the expected commit message after push.

### credential-encryption.md

1. The validate-inputs cell fails with a clear message for each missing variable.
2. The validate-inputs cell rejects invalid `CRED_MODE` values (anything other than `enable` or `migrate`).
3. After `CRED_MODE=enable` run: `grep -E "^crypt" configuration/config.yaml` outputs `crypt: true` and `crypt_backend: SOPS`.
4. After the test commit, `git show HEAD -- <cred-file> | grep -c "sops:"` outputs `1`.
5. `head -5 <cred-file>` on the local copy shows plain YAML content.
6. Re-running the guide does not fail: venv creation cell is idempotent; key generation cell is idempotent.

### dot-notated-parameter-migration.md

1. `npx runme run --all` exits 0 when run against a directory with no dot-notation keys.
2. After migration, `python3 yaml.safe_load` over all YAML files exits 0.
3. The `grep` re-scan after editing outputs `OK: no dot-notation parameter keys found`.

### configure-cloud-artifact-registries.md

1. The validate-inputs cell fails when `PROVIDER` is unset or invalid.
2. The validate-inputs cell fails for missing AWS vars when `PROVIDER=aws` or `both`; GCP vars are not checked.
3. The validate-inputs cell fails for missing GCP vars when `PROVIDER=gcp` or `both`; AWS vars are not checked.
4. `GCP_SA_KEY_FILE` existence check in validate-inputs fails with a clear error if the file is not found.
5. After `PROVIDER=aws` run: `cat configuration/registry_definitions/$AWS_REGDEF_NAME.yaml` shows actual values.
6. After `PROVIDER=gcp` run: `cat configuration/registry_definitions/$GCP_REGDEF_NAME.yaml` shows actual values.
7. After `PROVIDER=both` run: `ls configuration/registry_definitions/` shows both files; individual creation cells were skipped.
8. `git log --oneline -1` shows the expected commit message after push.

---

## Part 5 — Conclusions

### What the approach requires from the guide text

Seven requirements apply across all six guides:

1. **Every scriptable action in a `bash` block.** Prose and `text` blocks cannot be executed. Every `mkdir`,
   `cat >`, `git`, `openssl`, `python3`, and `grep` call must appear in a fenced `bash` block.

2. **A `Required Inputs` section with a table and a `KEY=value` template.** This is the single input contract
   between the guide and its callers. The table documents what each variable means; the template is what a user
   (or agent) fills in and sources before running.

3. **`:?` validation as the first runnable cell.** Required variables use `:?` (fail fast with a message);
   optional variables with a safe default use `${VAR:-default}`. For multi-provider guides, validation must be
   conditional — only validate variables relevant to the active selection.

4. **Manual-step callouts on every GUI/pipeline action.** Blockquotes with the prefix
   `> **Manual step — cannot be automated:**` are not bash blocks — runme skips them automatically, and AI
   agents treat them as stop signals.

5. **A verification command after every step that changes state.** Exit code 0 is not sufficient. File creation
   needs `cat`; git operations need `git log`; pipeline output needs `git pull` + `ls`.

6. **Real, working example content.** Schema placeholders, `<angle-bracket>` tokens, and hardcoded example
   values (committed without `$VAR`) break both human use and automation.

7. **`if/fi` guard form for all conditional cells.** `[ "$VAR" != "value" ] && { exit 0; }` exits with the
   test's exit code when the condition is false, causing runme and CI to report a cell failure. Only
   `if [ "$VAR" != "value" ]; then exit 0; fi` is safe — the `if/fi` form never propagates the test's exit code.

### What cannot run without external systems

- Any `git push` or `git pull` — requires a live GitLab instance and a valid token.
- Any `openssl s_client` against `$HOST:$PORT` — requires a live TLS service.
- Any pipeline-triggered verification (`git pull` after a GitLab job runs) — requires a CI pipeline to have
  completed first.
- `app_reg_def_process` output verification — visible only in GitLab job logs.
- AWS CodeArtifact and GCP Artifact Registry authentication — requires live cloud accounts.

### What cannot be automated at all

- GitLab UI operations: pipeline trigger, CI/CD variable configuration, token issuance, repository creation.
- Browser certificate export (GUI-only).
- Dot-notation YAML key renaming (text editing with context-dependent decisions).
- Observing pipeline-internal steps (EnvGene trust-store rebuild, `app_reg_def_process` job).
- Editing `credentials.yml` with secrets — format is machine-writable but secrets must be supplied by a human
  and the file must be encrypted before committing.

### Risk list

| Risk | Affected guide(s) | Mitigation |
|---|---|---|
| User forgets to source inputs, runs with no vars | all six | `:?` validation cell fails immediately with a named error |
| `cat > file <<EOF` in heredoc — variable not expanded if `<<'EOF'` | app-reg-defs, configure-cloud-artifact-registries | Guides use unquoted `<<EOF`; shell expands `$VAR` correctly |
| `grep \s\+` pattern — POSIX BRE not portable to macOS BSD grep | dot-notated-parameter-migration | Add `-E` flag for extended regex portability if needed |
| Token scope insufficient | app-reg-defs, configure-resource-profiles, credential-encryption, configure-cloud-artifact-registries | `git push` exits non-zero; add a pre-push token scope check if needed |
| Secret variable in input file committed | all six | Gitignore the input file; use GitLab CI/CD protected variables for secrets |
| Runme version skew between local and CI | all six | Pin `npx runme@<version>` in CI job script |
| AWS CodeArtifact untested end-to-end | configure-cloud-artifact-registries (aws/both) | Guide notes this warning; validate against a real CodeArtifact repo before relying on it in production |
| GCP `sa-key.json` not on disk at run time | configure-cloud-artifact-registries (gcp/both) | `GCP_SA_KEY_FILE` existence check in validate-inputs exits 1 with a clear message |
| `PROVIDER=both` with missing GCP vars after AWS-only prior run | configure-cloud-artifact-registries | validate-inputs checks both provider var sets when `PROVIDER=both`; fails before any file is created |
| Python venv already exists on re-run | credential-encryption | `if [ ! -d ".git_hook_venv" ]` guard skips `python3 -m venv` if venv already exists |
