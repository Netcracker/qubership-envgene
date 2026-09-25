# How to Run How-To Guides with runme

This document explains how to execute any EnvGene how-to guide that contains runnable `bash` blocks — from the
command line, VS Code, a GitLab CI pipeline, or an AI agent — using `npx runme`.

- [How to Run How-To Guides with runme](#how-to-run-how-to-guides-with-runme)
  - [Why npx — no installation required](#why-npx--no-installation-required)
  - [Quick start](#quick-start)
  - [Step 1 — Create your input file](#step-1--create-your-input-file)
  - [Step 2 — Run the guide](#step-2--run-the-guide)
  - [Running from the CLI](#running-from-the-cli)
  - [Running in VS Code](#running-in-vs-code)
  - [Running in a GitLab CI pipeline](#running-in-a-gitlab-ci-pipeline)
  - [Running with an AI agent](#running-with-an-ai-agent)
  - [Useful runme flags](#useful-runme-flags)
  - [Troubleshooting](#troubleshooting)

---

## Why npx — no installation required

`npx` ships with Node.js (v16+) and runs npm packages without installing them globally. If Node.js is available,
you can run any guide immediately — no separate runme install needed.

> **Note:** Use `npx runme` (the `runme` npm package). Do not use `npx @runme/cli` — that is a different package
> with a different flag set.

---

## Quick start

```bash
# 1. Copy the input template from the guide's "Required Inputs" section into a file
cat > my-inputs.txt <<EOF
APP_NAME=payment-service
REGISTRY_NAME=nexus-prod
EOF

# 2. Source the file to load variables, then run the guide
(set -a; source my-inputs.txt; npx runme run --all --filename docs/how-to/app-reg-defs-add-without-template.md)
```

---

## Step 1 — Create your input file

Each guide has a **Required Inputs** section containing:

- A table listing every variable (name, required/optional, example, description)
- A **Template** block you can copy as-is

The file format is plain `KEY=value`, one per line. Comments start with `#`. Any filename works — `.txt`, `.env`,
`prod-inputs.conf` — the name does not matter.

```
# my-inputs.txt
APP_NAME=payment-service        # no quotes needed
REGISTRY_NAME=nexus-prod
CLUSTER_NAME=prod-eu
ENV_NAME=prod-env-01
```

Rules:
- No `export` keyword — just `KEY=value`
- No shell expansion (`$OTHER_VAR` is not resolved inside the file)
- Blank lines and `#` comment lines are ignored
- Values with spaces should be quoted: `ENV_NAME="my env name"`

---

## Step 2 — Run the guide

```bash
(set -a; source my-inputs.txt; npx runme run --all --filename docs/how-to/<guide-name>.md)
```

How this works:
- `set -a` — marks every variable assigned in the sourced file for automatic export
- `source my-inputs.txt` — loads all `KEY=value` lines as shell variables
- `npx runme run --all` — runs every bash cell in document order; the process inherits the exported variables
- The outer `(...)` subshell keeps the variables isolated so they do not leak into your current shell session

Steps marked `> **Manual step — cannot be automated:**` in the guide are plain blockquotes, not bash cells —
runme skips them automatically. Complete those steps by hand before continuing past them.

---

## Running from the CLI

**Run all cells with an input file:**

```bash
(set -a; source certs-inputs.txt; npx runme run --all --filename docs/how-to/configure-system-certificates.md)
```

**Run a single named cell** (useful for re-running one step after a failure):

```bash
(set -a; source my-inputs.txt; npx runme run --filename docs/how-to/configure-system-certificates.md validate-inputs)
```

Cells are named by the first comment line inside the bash block (e.g. `# validate-inputs`). If a cell has no name
comment, runme assigns a sequential name — use `npx runme list --filename <guide>.md` to see all cell names.

**Pass variables inline** (no file — quick test with default values from the guide):

```bash
APP_NAME=test-app REGISTRY_NAME=test-registry \
  npx runme run --all --filename docs/how-to/app-reg-defs-add-without-template.md
```

**Override a single variable from an existing file:**

```bash
# Source the shared file, then override one variable for this run
(set -a; source shared-inputs.txt; ENV_NAME=prod-env-02 npx runme run --all \
  --filename docs/how-to/configure-resource-profiles.md)
```

**List all runnable cells in a guide:**

```bash
npx runme list --filename docs/how-to/configure-system-certificates.md
```

---

## Running in VS Code

1. Install the [Runme extension](https://marketplace.visualstudio.com/items?itemName=stateful.runme) from the
   VS Code marketplace.

2. Open any guide `.md` file — bash cells render with a **▶ Run** button.

3. Before clicking Run on any step cell, run the **Required Inputs** validation cell first. You can either:

   - **Edit the validation cell** to export your real values directly, then run it, or
   - **Open a terminal** in VS Code, `export` your variables, and then run cells — the extension shares the
     terminal environment.

4. Click **▶ Run** on each cell in order. Manual-step blockquotes have no Run button — complete them in the
   GitLab UI before continuing.

**Tip:** To pass an env file from VS Code, open the integrated terminal and run:

```bash
npx runme run --all --filename docs/how-to/<guide>.md --env-file my-inputs.txt
```

This is equivalent to clicking Run on all cells in order and uses your input file automatically.

---

## Running in a GitLab CI pipeline

Define a CI job that sets the required variables and calls `npx runme`:

```yaml
# .gitlab-ci.yml
run-guide:
  image: node:20
  variables:
    APP_NAME: "payment-service"
    REGISTRY_NAME: "nexus-prod"
  script:
    - npx runme run --all
        --filename docs/how-to/app-reg-defs-add-without-template.md
  only:
    - main
```

CI/CD variables defined at project level (Settings → CI/CD → Variables) are automatically available as environment
variables in every job. Because the guides use `:?` validation (not hardcoded defaults), the job fails immediately
with a clear error message if a required variable is missing — no silent wrong-value runs.

**Using a shared inputs file checked into the repo** (useful for non-secret values):

```yaml
run-guide:
  image: node:20
  script:
    - npx runme run --all
        --filename docs/how-to/configure-resource-profiles.md
        --env-file ci/inputs/resource-profiles.txt
```

**Secret values** (tokens, keys) should always come from GitLab CI/CD protected variables, not from files in the
repository.

---

## Running with an AI agent

An AI agent (such as Claude Code) executes guides by:

1. Reading the guide and identifying the **Required Inputs** table.
2. Asking the user for the actual values (or reading them from the conversation context).
3. Writing a `KEY=value` input file with the provided values.
4. Running the guide via `npx runme run --all --env-file <inputs-file>`.
5. Checking the `# Expected:` comment after each verification command against the actual output.
6. Stopping and reporting to the user when a step marked **Manual step** is reached.

The **Required Inputs** table and `# Expected:` comments in verification cells are the two structures the agent
relies on to run a guide correctly without guessing.

---

## Useful runme flags

| Flag | Purpose |
|---|---|
| `--all` | Run all bash cells in document order |
| `--filename <path>` | Path to the markdown guide file |
| `--env KEY=VALUE` | Set a single variable (repeatable) |
| `--env-file <path>` | Load variables from a `KEY=value` file |
| `--dry-run` | Print the commands that would run without executing them |
| `--skip-prompts` | Run non-interactively (useful in CI) |

**List cells without running:**

```bash
npx runme list --filename docs/how-to/<guide>.md
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `VAR is required — see Required Inputs section` | A required variable was not set | Add the variable to your input file and re-run |
| `must provide at least one command to run` | Positional args after `--filename` are treated as cell names, not variables | Use `--env KEY=val` or `--env-file` instead of bare `KEY=val` |
| Cell runs with example default instead of real value | Variable not exported before running, or `--env-file` not passed | Pass `--env-file` or `export VAR=value` before running |
| Manual step cell has a Run button | Unlikely — manual steps are blockquotes, not bash blocks | If you see this, the callout is missing the `>` prefix |
| `npx: command not found` | Node.js is not installed | Install Node.js v16+ from [nodejs.org](https://nodejs.org) |
| `git push` fails with auth error | Token scope insufficient | Ensure the token has `api`, `read_repository`, `write_repository` scopes |
