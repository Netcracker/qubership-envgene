# EnvGene — Repository Overview

EnvGene is a git-native tool that generates and versions cloud environment configurations from Jinja2 templates. It bridges a **Template Repository** (Jinja templates) and an **Instance Repository** (per-environment generated YAML + credentials) to produce an **Effective Set** consumed by ArgoCD/deployers.

## Module Map

| Directory | Purpose |
|-----------|---------|
| `python/envgene/` | `envgenehelper` pip package — core Python library shared by all modules |
| `python/artifact-searcher/` | Async Maven artifact URL resolver (multi-cloud auth) |
| `python/jschon-sort/` | JSON schema-ordered YAML key sorting |
| `python/integration/` | Thin config loader for external integrations |
| `build_effective_set_generator/` | Docker image + scripts that run the Effective Set generator (Java CLI wrapper) |
| `build_envgene/` | Docker image + scripts for the envgene pipeline jobs (env build, git commit, cred diff minimization) |
| `creds_rotation/` | Credential rotation pipeline job |
| `base_modules/` | Shared shell decrypt scripts included by other modules |
| `schemas/` | JSON schemas for all EnvGene objects (validated at runtime) |
| `scripts/` | Shared shell/Python utilities (certs, ES CLI runner, pipeline params) |
| `docs/` | Comprehensive documentation — start with `docs/envgene-objects.md` and `docs/envgene-configs.md` |

## Core Concepts

- **Template Repository** → Jinja2 templates for Tenant/Cloud/Namespace/Application objects, ParameterSets, ResourceProfiles, Registry/Application Definitions.
- **Instance Repository** → `environments/<cluster>/<env>/` tree: `Inventory/env_definition.yml`, `Namespaces/`, `Credentials/credentials.yml`, `Inventory/solution-descriptor/sd.yaml`.
- **Effective Set** → `effective-set/{topology,pipeline,deployment,runtime,cleanup}/` — final YAML for deployers.
- **Solution Descriptor (SD)** — list of `application:version` + `deployPostfix` entries driving ES generation. Merge modes: `basic-merge`, `extended-merge`, `basic-exclusion-merge`, `replace`.

## Key Environment Variables (runtime)

- `CI_PROJECT_DIR` — root of the instance repository
- `FULL_ENV_NAME` — `<cluster>/<env-name>`; `CLUSTER_NAME` and `ENVIRONMENT_NAME` are its split parts
- `SECRET_KEY` — Fernet encryption key; `ENVGENE_AGE_PRIVATE_KEY` / `PUBLIC_AGE_KEYS` for SOPS/AGE
- `SD_DATA` / `SD_VERSION` / `SD_REPO_MERGE_MODE` — Solution Descriptor inputs
- `EFFECTIVE_SET_CONFIG` — JSON config for the ES generator
- `ENV_NAMES` — multi-value `<cluster>/<env>` list for batch operations
- `ENVGENE_LOG_LEVEL` — logging verbosity

## Credentials

All credential files (matching `*credentials*.yml`, `*creds*.yml` in `Credentials/` or `configuration/`) are encrypted at rest. Encryption backend is configured in `configuration/config.yml` (`crypt_backend: Fernet | SOPS`). The `type` field is never encrypted.

## Tests

Each Python sub-package has its own pytest suite. Run from its directory:
```bash
cd python/envgene && python -m pytest
cd build_effective_set_generator/scripts && python -m pytest
cd build_envgene/scripts && python -m pytest
cd creds_rotation/scripts && python -m pytest
```

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
