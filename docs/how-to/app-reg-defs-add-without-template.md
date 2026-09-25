# Add an Application or Registry Definition without a template

This guide shows how to add a new Application Definition (AppDef) or Registry Definition (RegDef) to an instance
repository without modifying the template repository. The new definition is provided as a YAML file under
`/configuration/` and is added to the effective definitions during the next pipeline run.

For background on the definition override mechanism, see
[Application and Registry Definition - Definition overrides](/docs/features/app-reg-defs.md#definition-overrides).

## Running this guide

**No installation needed** — run with `npx`. Fill in your values using the template in [Required Inputs](#required-inputs), save to any file (e.g. `my-inputs.txt`), then run:

`(set -a; source my-inputs.txt; npx runme run --all --filename app-reg-defs-add-without-template.md)`

See [How to run guides with runme](/docs/how-to/how-to-run-guides-with-runme.md) for full CLI, VS Code, pipeline, and AI agent instructions.

Steps marked **Manual step — cannot be automated** are blockquotes — runme skips them automatically.

## Prerequisites

- Write access to the environment instance repository, cloned locally.
- Git and Node.js (v16+) available locally.

Verify tools are available:

```bash
git --version
# Expected: git version x.x.x
node --version
# Expected: v16.x.x or higher
```

## Required Inputs

Create a file with your values (any filename, e.g. `my-inputs.txt`) and load it with `source` before running.

| Variable | Required | Example | Description |
|---|---|---|---|
| `APP_NAME` | Yes | `payment-service` | Identifier used as the file name and in AppDef fields |
| `REGISTRY_NAME` | Yes | `nexus-prod` | Registry this application resolves artifacts from |

**Template** — copy, fill in your values, save as any filename:

```bash {"excludeFromRunAll":true,"name":"input-template"}
APP_NAME=my-new-app
REGISTRY_NAME=my-registry
```

Validate inputs (first runnable cell — fails immediately if a required variable is missing):

```bash
# validate-inputs
: "${APP_NAME:?APP_NAME is required — see Required Inputs section}"
: "${REGISTRY_NAME:?REGISTRY_NAME is required — see Required Inputs section}"
echo "Inputs OK: APP_NAME=$APP_NAME  REGISTRY_NAME=$REGISTRY_NAME"
```

## Steps

These steps assume the guide file is placed in the root of your instance repository.

1. **Create the YAML file in the instance repository.**

For a new AppDef, create `configuration/appdefs/$APP_NAME.yml`:

```bash
mkdir -p configuration/appdefs
cat > "configuration/appdefs/$APP_NAME.yml" <<EOF
name: $APP_NAME
artifactId: $APP_NAME
groupId: org.example
registryName: $REGISTRY_NAME
EOF
```

Verify the file was written with values substituted (not literal `${APP_NAME}` strings):

```bash
cat "configuration/appdefs/$APP_NAME.yml"
# Expected: YAML with actual values for name, artifactId, groupId, registryName
```

For a new RegDef, create `configuration/regdefs/$REGISTRY_NAME.yml`:

```bash
mkdir -p configuration/regdefs
cat > "configuration/regdefs/$REGISTRY_NAME.yml" <<EOF
name: $REGISTRY_NAME
credentialsId: my-creds
mavenConfig:
  fullRepositoryUrl: https://maven.example.com/repository
EOF
```

Verify:

```bash
cat "configuration/regdefs/$REGISTRY_NAME.yml"
# Expected: YAML with actual values for name, credentialsId, and mavenConfig
```

Use a filename that does **not** match any existing template-rendered definition in `/appdefs/` or `/regdefs/`. If
the filename matches, the definition override will **replace** the template-rendered one instead of adding a new one.

For the full set of required and optional fields, see
[Application Definition](/docs/envgene-objects.md#application-definition) and
[Registry Definition](/docs/envgene-objects.md#registry-definition).
If the registry uses AWS CodeArtifact or GCP Artifact Registry, see
[Configure cloud artifact registries](/docs/how-to/configure-cloud-artifact-registries.md) for authentication setup.

2. **Commit and push** the new file to the instance repository.

```bash
git add configuration/appdefs/ configuration/regdefs/
git commit -m "Add definition override for $APP_NAME"
git push
```

Verify the commit was created:

```bash
git log --oneline -1
# Expected: commit message matching "Add definition override for <your APP_NAME>"
```

3. **Trigger the instance pipeline.**

   > __Manual step — cannot be automated:__ Trigger the pipeline from the GitLab UI or via the API.
   > The `app_reg_def_process` job picks up the definition override and adds it as a new effective definition.

4. **Verify** the new effective definition appears after the pipeline completes.

Pull the latest changes from the remote:

```bash {"excludeFromRunAll":true}
git pull
```

Confirm the output file was written for an AppDef:

```bash {"excludeFromRunAll":true}
ls appdefs/
# Expected: $APP_NAME.yml appears in the listing
```

Inspect the contents:

```bash {"excludeFromRunAll":true}
cat "appdefs/$APP_NAME.yml"
# Expected: contents match your configuration/appdefs/$APP_NAME.yml
```

For a RegDef, check the `regdefs/` directory instead:

```bash {"excludeFromRunAll":true}
ls regdefs/
# Expected: $REGISTRY_NAME.yml appears in the listing
```

## Notes

- Definition overrides are plain YAML used as-is. They are **not** rendered as Jinja templates.
- Definition overrides apply repository-wide, not per-environment.
- The new definition is available to downstream pipeline processing (CMDB export, Generate Effective Set) in the same
   way as template-rendered definitions.

## Related

- [Application and Registry Definition (feature)](/docs/features/app-reg-defs.md) - full specification
- [UC-ARD-DO-3](/docs/use-cases/app-reg-defs.md#uc-ard-do-3-add-new-definition-via-definition-override-with-no-matching-template) - use case scenario
