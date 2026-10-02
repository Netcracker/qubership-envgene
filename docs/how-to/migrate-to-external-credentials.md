# Migrate credentials to an external Secret Store

Move EnvGene credentials out of Git and into an external Secret Store with the migration CLI.
After migration, each Credential in Git has `type: external` and keeps only `remoteRefPath` and `create`.
The Secret Store holds the values.

Run the three phases in order:

1. Migrate the Template repository and publish a new Template version.
2. Migrate the Instance repository.
3. Copy credential values into the Secret Store.

You can take the values from Git or from Jenkins.
The commands differ only where you record the source, where you collect Git values,
and where you match values before the Secret Store write.
Renaming credentials is out of scope.

- [Migrate credentials to an external Secret Store](#migrate-credentials-to-an-external-secret-store)
  - [Before you start](#before-you-start)
  - [Prepare the working environment](#prepare-the-working-environment)
    - [Install the CLI](#install-the-cli)
    - [Set the paths](#set-the-paths)
  - [Prepare the Instance repository](#prepare-the-instance-repository)
    - [Update the EnvGene version](#update-the-envgene-version)
    - [Create the Secret Store configuration](#create-the-secret-store-configuration)
    - [Configure access to the Secret Store](#configure-access-to-the-secret-store)
    - [Move system credentials](#move-system-credentials)
  - [Migrate the Template repository](#migrate-the-template-repository)
    - [Build the Template plan](#build-the-template-plan)
    - [Review the Template plan](#review-the-template-plan)
    - [Remove technical macros](#remove-technical-macros)
    - [Apply the Template plan and publish](#apply-the-template-plan-and-publish)
  - [Migrate the Instance repository](#migrate-the-instance-repository)
    - [Choose where the values are](#choose-where-the-values-are)
    - [Build the Instance plan](#build-the-instance-plan)
    - [Review the Instance plan](#review-the-instance-plan)
    - [Record decisions](#record-decisions)
    - [Collect credential values](#collect-credential-values)
    - [Apply the Instance plan](#apply-the-instance-plan)
    - [Point the Instance at the published Template](#point-the-instance-at-the-published-template)
  - [Copy values into the Secret Store](#copy-values-into-the-secret-store)
  - [Check generation](#check-generation)

## Before you start

- Python 3.12.
- Clones of the Template repository and the Instance repository, each on its own migration branch.
- A Secret Store and a service account that can write to it.
- Permission to set CI/CD variables on the Instance repository and to run its pipeline.
- The migration kit directory `external-creds-migration-skills/migration-skills`.

See [External Credentials](/docs/features/external-creds.md) for the Credential and Secret Store model.

## Prepare the working environment

### Install the CLI

Do this once.

If Python is not 3.12, create a virtual environment:

```powershell
py -3.12 -m venv C:\venvs\env312
```

Activate it in every new terminal:

```powershell
C:\venvs\env312\Scripts\Activate.ps1
```

Install the kit. `<kit>` is the path to `migration-skills`. Installation takes several minutes.

```powershell
python -m pip install -e "<kit>\scripts\cli[decrypt]" -e "<kit>\scripts\external-cred-provision" ruamel.yaml
```

The `[decrypt]` extra installs Fernet support.
If credential files use Fernet, set `SECRET_KEY` before `collect` and `collect-system`.
If they use SOPS, install the `sops` CLI and set `SOPS_AGE_KEY` or `ENVGENE_AGE_PRIVATE_KEY`.

### Set the paths

Do this in every new terminal. Replace the placeholders:

```powershell
$KIT      = "<path>\external-creds-migration-skills\migration-skills"
$TEMPLATE = "<path to the Template repository>"
$INSTANCE = "<path to the Instance repository>"
$OUT      = "<directory outside both repositories>"
New-Item -ItemType Directory -Force $OUT | Out-Null
$env:PYTHONPATH = "$KIT\scripts\python"
cd $OUT
```

The CLI writes credential values and logs under `$OUT`.
Do not commit those files. Delete `$OUT` after the migration.

## Prepare the Instance repository

### Update the EnvGene version

Update the Instance repository to an EnvGene version that supports External Credentials
and the pipeline parameter `EXTERNAL_CREDENTIAL_PROVISIONING`.
Commit the change.

### Create the Secret Store configuration

Do this once for the Instance repository.

Create `configuration/secret-stores.yml` with one store, `default_store`.
For GCP:

```powershell
@"
default_store:
  type: gcp
  projectId: <GCP project ID>
"@ | Set-Content -Encoding ascii "$INSTANCE\configuration\secret-stores.yml"
```

For another store, change `type` and its required field.
The [secret stores schema](/schemas/secret-stores.schema.json) lists the fields.

| `type`  | Required field |
|---------|----------------|
| `gcp`   | `projectId`    |
| `vault` | `mountPath`    |
| `aws`   | `region`       |
| `azure` | `vaultName`    |

### Configure access to the Secret Store

Set the variables for your store type in the Instance repository CI/CD settings and in the terminal.

| `type`  | Variables                                                          |
|---------|--------------------------------------------------------------------|
| `gcp`   | `GOOGLE_APPLICATION_CREDENTIALS`                                   |
| `vault` | `VAULT_ADDR`, `VAULT_TOKEN`                                        |
| `aws`   | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION` |
| `azure` | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`        |

### Move system credentials

Credentials under `configuration/credentials/` are required by the pipeline, so move them first.
The CLI writes them at the Secret Store path `global`. You cannot choose another path.

Collect them:

```powershell
migration-cli collect-system --instance-root $INSTANCE --out $OUT\system-context.yml --strategy create_if_absent
```

Check Secret Store access without writing:

```powershell
external-cred-provision --dry-run $OUT\system-context.yml
```

Create the credentials:

```powershell
external-cred-provision $OUT\system-context.yml
```

`--strategy` accepts:

- `create_if_absent` creates a credential when it is missing and leaves an existing one unchanged.
- `overwrite` creates or replaces a credential. This is the default.

The CLI skips a credential whose value is `envgeneNullValue`.

## Migrate the Template repository

### Build the Template plan

```powershell
python -m envgene_migrate plan --repo=template --root $TEMPLATE --manual
```

The CLI writes `migration-plan.yaml` at the Template repository root and prints a summary.
Apply the plan when the summary says `BLOCKERS: none`.

> [!NOTE]
> `DECISIONS NEEDED` stays in the summary after you review the plan.
> Edit `migration-plan.yaml`, then run apply.

### Review the Template plan

Check every credential under `to_review` and `to_confirm`.
Edit `migration-plan.yaml` when a value is wrong, then save the file.

- `create: true` tells EnvGene to create the credential with a random value when it is
  missing from the Secret Store. `create: false` means the credential must already be
  there. EnvGene only checks that it exists.
- `remoteRefPath` is the path prefix in the Secret Store. `{{ current_env.cloud }}` is
  one credential per cluster. `{{ current_env.cloud }}/{{ current_env.name }}` is one
  credential per environment.
- `includeInCredentialTemplate: false` leaves the credential out of the Credential Template.

For example:

```yaml
to_review:
  maas:
    remoteRefPath: '{{ current_env.cloud }}'
    create: false
    includeInCredentialTemplate: true
```

Read `stale_credential_template_entries`.
Apply removes those credentials from the Credential Template.
Add a credential back to the plan if you still need it.

Do not rename credential keys.
`suggestions` explains the CLI choice and does not change the migration.

### Remove technical macros

Do this when `runtime_credential_macros` is not empty.

That block lists credential macros inside technical parameters.
The migration does not rewrite them, and the pipeline fails on those files after cutover.
Remove the macros:

```powershell
python -m envgene_migrate strip-technical-macros --repo=template --root $TEMPLATE
```

Commit the result and build the Template plan again.

> [!NOTE]
> If a technical parameter cannot work without the credential, that case is outside this how-to.
> Contact the EnvGene team.

### Apply the Template plan and publish

```powershell
python -m envgene_migrate apply --repo=template --root $TEMPLATE --manual
```

Commit the result and publish the Template.
Record the published `name:version`. You need it when you point the Instance at that Template.

`apply` refuses a dirty Git working tree for tracked files.
Commit or stash those changes first. Untracked files do not block `apply`.

## Migrate the Instance repository

### Choose where the values are

Do this before the first Instance `plan`.
Create `migration-plan.yaml` at the Instance repository root.
Use `git` when the values are in Git, or `jenkins` when they are in Jenkins:

```powershell
@"
operator_decisions:
  values_source: git
"@ | Set-Content -Encoding ascii "$INSTANCE\migration-plan.yaml"
```

The CLI also accepts `store` and `apply_store`.
This how-to covers `git` and `jenkins`.

### Build the Instance plan

```powershell
python -m envgene_migrate plan --repo=instance --root $INSTANCE --manual
```

The CLI fills in `migration-plan.yaml` and keeps `operator_decisions`.

### Review the Instance plan

Check `create` and `remoteRefPath` the same way as in the Template plan.
Defaults:

| Credential source   | `create` | `remoteRefPath`   |
|---------------------|----------|-------------------|
| Cloud Passport      | `false`  | `<cluster>`       |
| System              | `false`  | `global`          |
| Environment         | `true`   | `<cluster>/<env>` |
| Shared, environment | `true`   | `<cluster>/<env>` |
| Shared, cluster     | `true`   | `<cluster>`       |
| Shared, repository  | `true`   | `global`          |

Write the path without a leading `/`.
For one credential per namespace, add a segment: `<cluster>/<env>/<namespace>`.

Leave `writeToStore: false`.
Values go to the Secret Store when you copy them in the next phase.

### Record decisions

Open the end of `migration-plan.yaml`.
For each list that is not empty, add the matching field under `operator_decisions` and save the file.

| Non-empty list                        | Field                    | What to set                                      |
|---------------------------------------|--------------------------|--------------------------------------------------|
| `to_delete.deployer_credentials`      | `deployer_delete`        | `false` keeps the files. `true` deletes them     |
| `to_delete.unused_shared_credentials` | `unused_shared_delete`   | `false` keeps the files. `true` deletes them     |
| `runtime_credential_macros`           | `technical_macros_waive` | `true` when the Template is already updated      |

`deployer_delete: true` also removes `inventory.deployer`.
`false` keeps `app-deployer/*-creds.yml`.

For example, keep deployer files and leave the other lists empty:

```yaml
operator_decisions:
  values_source: git
  deployer_delete: false
```

`apply` always deletes `<env>/Credentials/credentials.yml` files listed in `to_delete.generated_env_credentials`.
The pipeline generates them again.

### Collect credential values

Do this only for `values_source: git`.
Skip it for Jenkins.

Collect before you apply the Instance plan, while the values are still in Git:

```powershell
migration-cli collect --instance-root $INSTANCE --out $OUT\cred-values.yaml
```

System credentials are not in this file. You already moved them.

### Apply the Instance plan

Commit the Instance repository, then:

```powershell
python -m envgene_migrate apply --repo=instance --root $INSTANCE --manual
```

The CLI sets credentials to `type: external`, replaces `creds.get` macros with `credRef`,
and deletes the files in `to_delete`.
Commit the result.

### Point the Instance at the published Template

Do this before you copy values into the Secret Store.
The previous Template still contains `creds.get` macros, and generation fails on it.

Set `envTemplate.artifact` in every `environments/**/Inventory/env_definition.yml`
to the published `name:version`, then check:

```powershell
python -m envgene_migrate check-template-version --repo=instance --root $INSTANCE --expect "<name:version>"
```

Commit the result.

## Copy values into the Secret Store

Run the Instance pipeline on the migration branch with:

| Parameter                          | Value             |
|------------------------------------|-------------------|
| `ENV_NAMES`                        | `<cluster>/<env>` |
| `ENV_BUILDER`                      | `true`            |
| `GENERATE_EFFECTIVE_SET`           | `true`            |
| `EXTERNAL_CREDENTIAL_PROVISIONING` | `skip`            |

`skip` builds the External Credential Context and does not write the Secret Store.
When the pipeline commits, update the local branch:

```powershell
git -C $INSTANCE pull
```

Match the values to that context.

For `values_source: git`, use the file from the collect step:

```powershell
migration-cli fill --repo-root $INSTANCE --values $OUT\cred-values.yaml --values-format instance_scoped --out $OUT\filled.yaml --partial
```

For `values_source: jenkins`, export from Jenkins, then match:

```powershell
$env:JENKINS_USERNAME = "<username>"
$env:JENKINS_TOKEN    = "<token>"
```

```powershell
migration-cli export-credentials --tenant <tenant> --jenkins-url <jenkins-url> --out-dir $OUT\jenkins-export
```

```powershell
migration-cli fill --repo-root $INSTANCE --values-dir $OUT\jenkins-export --values-format jenkins_export --out $OUT\filled.yaml --partial
```

For several tenants, pass a comma-separated list: `--tenant <tenant1>,<tenant2>`.
Export needs access to the Jenkins Script Console.

`fill` writes only credentials with `create: false`.
Unmatched credentials go to `$OUT\filled-unmatched.yaml`.
When any credential is unmatched, `fill` still writes the files and exits with code 1.

Write the values:

```powershell
external-cred-provision $OUT\filled.yaml
```

## Check generation

Run the pipeline with the same parameters, but omit `EXTERNAL_CREDENTIAL_PROVISIONING` or set it to `apply`.

After the pipeline commits, open `environments/<cluster>/<env>/effective-set/`
and confirm that credential slots hold Secret Store references.
Run a trial deploy.
Merge the Template branch, then the Instance branch.
Delete `$OUT`.
