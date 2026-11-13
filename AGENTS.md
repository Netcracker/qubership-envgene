# AI Agent Rules for qubership-envgene Repository

Component ID: envgene

This document contains guidelines and rules for AI coding assistants working with this repository.
Claude Code reads it through `.claude/CLAUDE.md`, which imports this file.

## Repository overview

EnvGene is a Git-native tool that generates and versions cloud environment configurations from Jinja2 templates. It bridges a **Template Repository** (Jinja templates) and an **Instance Repository** (per-environment generated YAML + credentials) to produce an **Effective Set** consumed by ArgoCD/deployers.

### Module Map

This branch runs all pipeline jobs as **one consolidated job** (`scripts/pipeline/orchestrator.py::dispatch`), not as separate per-job Docker images/scripts. `dispatch()` runs `run_single_env_pipeline()` for one `ENV_NAMES` value, or fans out to parallel child processes via `multi_env_runner.fan_out()` when `ENV_NAMES` lists multiple environments. Most job logic lives under `scripts/`.

| Directory | Purpose |
| ----------- | --------- |
| `scripts/` | Single-job pipeline: `pipeline/` (orchestrator + params), `build_env/`, `cloud_passport/`, `creds_rotation/`, `effective_set/`, `bg_manage/`, `inventory/`, `sd/`, `build_template/`, `utils/`, `tests/`, `git_commit/` (`git_commit.py`); also `report.py` (moved here from `build_envgene/scripts/`) |
| `modules/envgene/` | `envgenehelper` pip package — core Python library shared by all modules |
| `modules/artifact-searcher/` | `artifact_searcher` pip package — async Maven artifact URL resolver (multi-cloud auth) |
| `modules/external-cred-provision/` | `external-cred-provision` pip package — provisions external credentials into secret stores; `src`-layout, console script `external-cred-provision` |
| `build_effective_set_generator/` | Java/Maven multi-module project (Quarkus CLI) — the Effective Set generator engine, invoked from `scripts/effective_set/` via `scripts/utils/run_effective_set_cli.sh` |
| `build_envgene/` | Docker image build context (`build_envgene/build/Dockerfile`) — no longer holds Python scripts, see `scripts/` above |
| `schemas/` | JSON schemas for all EnvGene objects (validated at runtime) |
| `docs/` | Comprehensive documentation — start with `docs/envgene-objects.md` and `docs/envgene-configs.md` |

**Removed from `main` in this branch** (no directory exists here for these; superseded by the single-job consolidation): the standalone `base_modules/`, top-level `creds_rotation/`, and `python/integration/` modules were dissolved into `envgenehelper`/`scripts/utils/`/`scripts/cloud_passport/` (credential rotation moved to `scripts/creds_rotation/` — see `scripts/CLAUDE.md`); `python/jschon-sort/` is now an external pip dependency (`jschon-tools`), not local source (see `modules/envgene/CLAUDE.md`). `python/` (main's name for the directory below) was renamed to `modules/` in this branch — same pip packages as before, just a clearer top-level name.

### Python module layout

`modules/envgene`, `modules/envgene-shared`, `modules/artifact-searcher`, `modules/external-cred-provision` are ordinary pip packages (`pyproject.toml` + `[build-system]`), installed editable (`pip install -e`) in dev/CI and plain (`pip install`) in the Docker image — see each `pyproject.toml`'s `[project] version`, which is a required-by-setuptools formality, not a tracked release version. None of them are ever published anywhere (no PyPI, no internal registry) — `pip install -e`/`pip install <dir>` only registers the package into the local `site-packages`, nothing leaves the machine. `scripts/` itself is not a package; it's resolved purely via `PYTHONPATH` (see `scripts/CLAUDE.md`). Directory-vs-package-name note: `modules/envgene` contains package `envgenehelper`; `modules/envgene-shared` contains package `envgene_shared`; `modules/artifact-searcher` contains package `artifact_searcher`; `modules/external-cred-provision/src` contains package `external_cred_provision`.

### Core Concepts

- **Template Repository** → Jinja2 templates for Tenant/Cloud/Namespace/Application objects, ParameterSets, ResourceProfiles, Registry/Application Definitions.
- **Instance Repository** → `environments/<cluster>/<env>/` tree: `Inventory/env_definition.yml`, `Namespaces/`, `Credentials/credentials.yml`, `Inventory/solution-descriptor/sd.yaml`.
- **Effective Set** → `effective-set/{topology,pipeline,deployment,runtime,cleanup}/` — final YAML for deployers.
- **Solution Descriptor (SD)** — list of `application:version` + `deployPostfix` entries driving ES generation. Merge modes: `basic-merge`, `extended-merge`, `basic-exclusion-merge`, `replace`.

### Key Environment Variables (runtime)

- `CI_PROJECT_DIR` — root of the instance repository
- `FULL_ENV_NAME` — `<cluster>/<env-name>`; `CLUSTER_NAME` and `ENVIRONMENT_NAME` are its split parts
- `ENVGENE_AGE_PRIVATE_KEY` / `PUBLIC_AGE_KEYS` — SOPS/AGE keys
- `SD_DATA` / `SD_VERSION` / `SD_REPO_MERGE_MODE` — Solution Descriptor inputs
- `EFFECTIVE_SET_CONFIG` — JSON config for the ES generator
- `ENV_NAMES` — multi-value `<cluster>/<env>` list for batch operations
- `ENVGENE_LOG_LEVEL` — logging verbosity

### Credentials

All credential files (matching `*credentials*.yml`, `*creds*.yml` in `Credentials/` or `configuration/`) are encrypted at rest. SOPS is the only encryption backend (`crypt_backend: SOPS` in `configuration/config.yml`). Fernet is used only to decrypt cloud discovery creds with the discovery project's `SECRET_KEY`. The `type` field is never encrypted.

## Change flow

The stage order and its gates are defined in the `envgene-orchestration` skill. Two rules apply to every agent:

- Implement does not start without the propose and design gate rows in `ledger.md`.
- The design (`openspec/changes/<id>/design.md`) is the one design artifact of a change. It defines every contract id it lists, and the plan covers each of them.

## Code review

Before any code review in this repository, load the `envgene-code-review` skill
(`.claude/skills/envgene-code-review/SKILL.md`). It holds the team review procedure and code rules.
Apply them in addition to any other review skill or command.

## Commands

### Writing documentation and text

All rules for how text is written in this repository - documentation under `docs/`, the readme files,
and prose for issues, change requests, and pull requests - live in the `writing-docs` skill at
`.claude/skills/writing-docs/`. Read that skill before you write or edit any `.md` file, any doc under
`docs/`, or any issue, CR, or PR prose for this repository. Its `SKILL.md` routes to the reference file
for the task: prose style, Markdown formatting, document structure, content integrity, object examples,
sample files, and use-case design.

### Tests

Each Python module has its own pytest suite, installed editable first (`pip install -e "modules/envgene[dev]"`, etc. — see `.github/actions/run-tests/action.yml`), then run from its own directory:

```bash
pip install -e "modules/envgene-shared[dev]"
pip install -e "modules/envgene[dev]"
pip install -e "modules/artifact-searcher[dev]"
pip install -e "modules/external-cred-provision"
cd modules/envgene-shared && python -m pytest envgene_shared/tests/
cd modules/envgene/envgenehelper && python -m pytest
cd modules/artifact-searcher/artifact_searcher && python -m pytest
cd modules/external-cred-provision && python -m pytest
```

The single-job pipeline scripts under `scripts/` (including `git_commit.py`/`report.py`, formerly under `build_envgene/scripts/`) are tested from the repository root the same way:

```bash
PYTHONPATH=".:./scripts" python -m pytest scripts/tests/
```

The Effective Set generator is a Maven project; from `build_effective_set_generator/`:

```bash
./mvnw test
```

### BDD End-to-End Tests

Cucumber BDD tests are located in the `cucumber_tests/` directory. These tests run the full pipeline orchestrated via Docker or a local Python environment.

```bash
cd cucumber_tests
./run_bdd_tests.sh
```

Or on Windows:

```powershell
cd cucumber_tests
.\run_bdd_tests.ps1
```

### OpenSpec validation

```bash
openspec validate <change-id> --strict --no-interactive
```

### Lint

CI runs super-linter (`.github/workflows/super-linter.yaml`, settings in `.github/super-linter.env`). The same checks
locally, with Docker available (the image tag matches the action version in the workflow):

```bash
docker run --rm -e RUN_LOCAL=true --env-file .github/super-linter.env -v "$(pwd)":/tmp/lint \
  ghcr.io/super-linter/super-linter:slim-v8.7.0
```

Not run in every environment: without Docker, record `lint: not run: no docker` in the ledger.

---

## Code Style

### YAML

- Use 2-space indentation
- Quote string values consistently
- Add comments for complex logic
- Use meaningful key names

## Commits and pull requests

### Commit messages

Use Conventional Commits format: `<type>: <description>`. Types in use here: `feat`, `fix`,
`docs`, `chore`, `refactor`, `test`, `ci`, `perf`, `style`. The repository convention is no
scope prefix.

Subject line:

- Imperative mood (`Add X`, not `Added X` or `Adds X`).
- Under 72 characters.
- No trailing period.

Body (when needed):

- Empty line before body.
- Explain WHY the change is needed and trade-offs, not WHAT (the diff already shows what).
- Wrap at 72 characters.
- Reference issues in a footer (`Closes #123`, `Refs #456`).

### Secret scanning

A pre-commit hook runs a secret scanner (CyberFerret) on every commit. Never bypass it. Do not add a
skip token to the commit message (`@cf_skip`, `@cf_ignore`, `@ignore_cf`, `@skip_cf`), do not pass
`git commit --no-verify`, and do not sidestep the hook by committing through the GitHub API or web
editor. If the hook blocks a commit, resolve the finding or make the scan runnable, for example by
setting the scanner's dictionary password. A blocked commit is a signal to investigate, not to skip.

### Commit type for docs-only changes

If a commit touches only documentation files (`*.md`, `AGENTS.md`, `.claude/CLAUDE.md`, files under `docs/`), use
`docs:` as the commit type. The post-merge build workflow skips Docker image rebuilds for commit types
other than `feat:`, `fix:`, and `BREAKING CHANGE`. A doc-only change marked `feat:` or `fix:` triggers
unnecessary image builds.

Tests and linters run on every PR regardless of commit type.

### Pull request description for docs-only changes

Documentation PRs omit the "Test plan" section by default. The doc-quality gates (super-linter,
textlint, link-checker, markdownlint) cover correctness. Include a Test plan section only when
explicitly requested or when the change has runtime implications beyond text.

### Commit granularity

**One logical change per commit.** A commit should be a single coherent unit that a reviewer
can read in one pass.

Split into separate commits when:

- A rule, convention, or schema is added (AGENTS.md, lint config) along with content that
  follows it - put the rule change in its own commit so the rule can be reviewed separately
  from its application.
- Mechanical changes (mass rename, formatting sweep) are mixed with semantic changes - put
  the mechanical change in its own commit so the semantic diff is readable.
- A pre-existing issue is fixed in passing - put the fix in its own commit so it can be
  backported or reverted independently.

Keep in the same commit:

- Test with the code or doc it covers.
- Migration script with the schema change that requires it.
- Anchor renames with the heading change that triggered them.

### Pull request scope

**One focused goal per PR.**

- PR description states the problem, the decision, and trade-offs.
- Target size: under 500 lines of changed prose for docs PRs, under 400 lines for code PRs.
  Larger changes belong in a stack of dependent PRs (mention the order in each description).
- Refactor PRs go separately from feature PRs. Rule additions go separately from
  rule-application PRs.
- Do not include unrelated cleanup. File a follow-up issue instead.

### Change requests

A change request (CR) is the implementation-phase issue. It hands a settled design to a
developer for implementation, not for design discussion or investigation. CRs follow a
six-section structure. For the body template, the convention, and good and bad examples, see
[docs/dev/creating-cr.md](/docs/dev/creating-cr.md).
