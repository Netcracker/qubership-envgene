# Migrating Dot-Notation Parameters to Nested Object Format

- [Migrating Dot-Notation Parameters to Nested Object Format](#migrating-dot-notation-parameters-to-nested-object-format)
  - [Running this guide](#running-this-guide)
  - [Problem](#problem)
  - [Migration Steps](#migration-steps)
  - [Example Migration](#example-migration)

This guide explains how to migrate parameters in [EnvGene objects](/docs/envgene-objects.md) that have a dot (`.`) in their key to a normalized YAML format.

## Running this guide

**No installation needed** — run with `npx`. Fill in your values using the template in [Required Inputs](#required-inputs), save to any file (e.g. `my-inputs.txt`), then run:

`(set -a; source my-inputs.txt; npx runme run --all --filename dot-notated-parameter-migration.md)`

See [How to run guides with runme](/docs/how-to/how-to-run-guides-with-runme.md) for full CLI, VS Code, pipeline, and AI agent instructions.

The find and verify steps in this guide are runnable. The key renaming itself is a manual text-editing step —
steps marked **Manual step — cannot be automated** are blockquotes that runme skips automatically.

## Required Inputs

Create a file with your values (any filename, e.g. `my-inputs.txt`) and load it with `source` before running.

| Variable | Required | Example | Description |
|---|---|---|---|
| `SEARCH_DIR` | No | `environments` | Root directory to scan for dot-notation parameters (default: `environments`) |

**Template** — copy, fill in your values, save as any filename:

```bash {"excludeFromRunAll":true,"name":"input-template"}
SEARCH_DIR=environments
```

Validate inputs (first runnable cell):

```bash
# validate-inputs
SEARCH_DIR="${SEARCH_DIR:-environments}"
echo "Inputs OK: SEARCH_DIR=$SEARCH_DIR"
```

## Problem

Some parameters use dots in their names (e.g., `database.url`) to describe complex parameters. Not all consumers of such parameters can process them correctly, which can cause issues in processing.

## Migration Steps

1. **Identify parameters with dots in their names.**

   Scan for YAML keys that contain a dot:

   ```bash
   grep -rn '^\s\+[a-zA-Z][a-zA-Z0-9_]*\.[a-zA-Z]' "$SEARCH_DIR" --include="*.yml" --include="*.yaml" \
     || echo "No dot-notation parameter keys found under $SEARCH_DIR"
   # Expected: lines showing file:linenum: key.with.dot: value
   # If the echo fires, no migration is needed.
   ```

   Review the output and note which files need editing.

2. **Convert each dotted key into nested YAML objects.**

   > **Manual step — cannot be automated:** Open each file identified above in your editor and rename the
   > dot-notation keys to nested YAML structure. See [Example Migration](#example-migration) below.

   From:

   ```yaml {"excludeFromRunAll":true}
   parameters:
     database.url: jdbc:mysql://host/db
     service.port: 8080
   ```

   To:

   ```yaml {"excludeFromRunAll":true}
   parameters:
     database:
       url: jdbc:mysql://host/db
     service:
       port: 8080
   ```

3. **Verify the edited files are valid YAML.**

   Check that each edited file parses without errors:

   ```bash
   python3 -c "
   import yaml, sys, glob
   files = glob.glob('$SEARCH_DIR/**/*.yml', recursive=True) + \
           glob.glob('$SEARCH_DIR/**/*.yaml', recursive=True)
   errors = []
   for f in files:
       try:
           yaml.safe_load(open(f))
       except yaml.YAMLError as e:
           errors.append(f'{f}: {e}')
   if errors:
       print('YAML errors found:')
       for e in errors: print(' ', e)
       sys.exit(1)
   else:
       print(f'All {len(files)} YAML files under $SEARCH_DIR parsed successfully')
   "
   # Expected: "All N YAML files ... parsed successfully"
   ```

   Confirm no dot-notation keys remain:

   ```bash
   grep -rn '^\s\+[a-zA-Z][a-zA-Z0-9_]*\.[a-zA-Z]' "$SEARCH_DIR" --include="*.yml" --include="*.yaml" \
     && echo "WARN: dot-notation keys still present — review the output above" \
     || echo "OK: no dot-notation parameter keys found"
   # Expected: "OK: no dot-notation parameter keys found"
   ```

4. **Apply the same change in all relevant places** and commit.

   ```bash
   git add "$SEARCH_DIR"
   git commit -m "Migrate dot-notation parameter keys to nested YAML"
   git push
   ```

   Verify the commit was created:

   ```bash
   git log --oneline -1
   # Expected: "Migrate dot-notation parameter keys to nested YAML"
   ```

## Example Migration

Given this original file:

```yaml {"excludeFromRunAll":true}
parameters:
  app.env: prod
  logging.level: INFO
```

Migrate to:

```yaml {"excludeFromRunAll":true}
parameters:
  app:
    env: prod
  logging:
    level: INFO
```

Keep the structure simple. Use nested keys instead of dot-notation.
