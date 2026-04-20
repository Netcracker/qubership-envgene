# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**EnvGene** (Environment Generator) is a git-based tool for generating and versioning environment configurations using templates. It manages parameters for many similar cloud environments via template-based provisioning, CI/CD integration, and encrypted credential management.

## Build and Test Commands

### Local Development (Docker-based)

```bash
make build-tests    # Build test container
make up-tests       # Start test container
make run-tests      # Run all tests inside container
make bash-tests     # Open shell in running test container
make down           # Stop all containers
```

### Running Tests Directly (Python 3.12 required)

Install dependencies first:

```bash
pip install --upgrade pip "setuptools<82" wheel
pip install --no-cache-dir -r dependencies/tests_requirements.txt
./python/build_modules.sh
pip install python/artifact-searcher
```

Run individual test suites:

```bash
# EnvGene helper
cd python/envgene/envgenehelper && pytest --capture=no -W ignore::DeprecationWarning

# Artifact searcher
cd python/artifact-searcher/artifact_searcher && pytest --capture=no -W ignore::DeprecationWarning

# Build env
cd scripts/build_env && pytest --capture=no -W ignore::DeprecationWarning

# Blue-green management
cd scripts/bg_manage && pytest --capture=no -W ignore::DeprecationWarning

# Credential rotation
cd creds_rotation/scripts && pytest --capture=no -W ignore::DeprecationWarning

# SBOM retention policy
cd build_effective_set_generator/scripts && pytest --capture=no -W ignore::DeprecationWarning
```

### Java (Effective Set Generator)

```bash
cd build_effective_set_generator && mvn package
```

## Architecture

The project is multi-language (Python 3.12 + Java/Maven) with these main components:

**`python/envgene/envgenehelper/`** - Core Pydantic-based library with data models and validation schemas. Primary dependency for all other Python modules.

**`python/artifact-searcher/`** - Async service for discovering build artifacts from AWS S3, GCP, and container registries.

**`scripts/build_env/`** - Main orchestrator that generates environment configs from templates. Handles Jinja2 rendering, YAML processing, and JSON schema validation.

**`build_effective_set_generator/`** - Java/Quarkus service that calculates effective parameter sets (Maven multi-module project). Translates GString templates to Jinjava.

**`scripts/bg_manage/`** - Blue-green deployment orchestration and state management.

**`creds_rotation/`** - Encrypted credential management using SOPS v3.9.0.

**`schemas/`** - 27 JSON Schema files that are the authoritative definition of all EnvGene objects (environments, templates, namespaces, applications, credentials, registries, etc.).

**`docs/`** - Documentation following the Diátaxis framework (how-to, explanation, reference, tutorials).

### Pyright Configuration

Extra paths configured in `pyrightconfig.json`: `python/envgene`, `python/artifact-searcher`, `python/integration`, `python/jschon-sort`.

## Code Style

- **Python**: Black (120 char line length), mypy strict mode, Python 3.12 type annotations
- **YAML**: 2-space indentation
- **Linting**: ruff, shellcheck, actionlint, checkov (IaC security), gitleaks (secret scanning)

## Documentation Standards (from AGENTS.md)

These rules apply whenever creating or editing Markdown documentation:

### Formatting

- **Lists**: MUST have empty lines before and after them (required by Markdown linters)
- **Dashes**: Always use `-` (hyphen-minus) in prose; never `—` (em dash) or `–` (en dash)
- **Callouts**: Use GitHub-native syntax: `> [!NOTE]`, `> [!WARNING]`, `> [!TIP]`, `> [!IMPORTANT]`, `> [!CAUTION]`
- **Tables**: All pipe characters (`|`) MUST be vertically aligned across all rows; simplify cell content if needed to achieve alignment
- **ToC**: Documents with 3+ headings need a Table of Contents immediately after the H1, as a plain list (no heading for the ToC itself)

### Object Examples

Before writing any YAML/JSON example for an EnvGene object:

1. Read the entry in `docs/envgene-objects.md`
2. Read the matching schema file in `schemas/`
3. Only include fields that exist in the schema; mark omitted fields with `# ...`
4. In tutorials/how-to guides, show only the relevant snippet - not the full object

### Documentation Structure (Diátaxis)

- `docs/how-to/` - Goal-oriented practical steps (~200-400 lines, minimal theory)
- `docs/explanation/` - Conceptual understanding, design decisions
- `docs/tutorials/` - Step-by-step learning with complete working examples
- Reference docs (object schemas, specs) - at `docs/` root level

### File Naming

- Markdown files: kebab-case (e.g., `override-template-parameters.md`)
- YAML files: kebab-case, descriptive (e.g., `billing-prod-deploy.yml`)
