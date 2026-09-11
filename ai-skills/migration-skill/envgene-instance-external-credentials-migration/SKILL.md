---
name: envgene-instance-external-credentials-migration
description: Migrate one EnvGene Instance Repository to External Credentials: analyse Environment Instances, select the first non-prod, update Cloud Passport, Shared, and System Credentials if needed, then prepare TEMPORARY, deployment, PERSISTENT, and rollout.
---

# EnvGene Instance External Credentials Migration

Guide the user through migration. On each run, read `external-credentials-migration-report.md`, complete the current step, update the report, and show one next action.

## Constraints

- Work only with the local repository and user data.
- Do not use the web, GitHub, remote documentation, or helper scripts.
- Never run a pipeline, deployment, TEMPORARY, PERSISTENT, commit, push, or merge.
- Do not access the Secret Store or request secret values or CI/CD variables.
- Do not output or copy values from `data`.
- Do not edit generated `environments/<cluster>/<env>/Credentials/credentials.yml`.

## 1. Select the first Environment Instance

If no environment is selected yet:

1. find all `environments/<cluster>/<env>/Inventory/env_definition.yml` files;
2. show for each:
   - `<cluster>/<env>`;
   - `envTemplate.name` and `envTemplate.artifact`;
   - `inventory.cloudPassport`;
   - `envTemplate.sharedMasterCredentialFiles`;
   - assumption: `likely non-prod`, `likely prod`, or `unknown`;
3. suggest up to three non-prod candidates;
4. ask the user to select one.

The user confirms the environment type.

## 2. Identify the related group

For the selected environment:

1. find all consumers of its Cloud Passport;
2. find all consumers of its Shared Credentials;
3. if the source is shared, suggest:
   - migrating all consumers together;
   - splitting the source first;
4. find System Credential files:
   - `/configuration/credentials/credentials.yml|yaml`;
   - `environments/<cluster>/app-deployer/*-creds.yml|yaml`;
5. record:

```text
Template migration status: NOT_VERIFIED
```

You cannot determine from the Instance Repository whether the Template has been updated.

## 3. Migration order

1. Obtain the concrete version of the updated Template.
2. Check the Secret Store.
3. Confirm that secrets exist in the external store.
4. Update Shared Credentials.
5. Update Cloud Passport Credentials.
6. Check matching `credId` values.
7. Decide whether to migrate System Credentials.
8. Prepare TEMPORARY.
9. Check the generated result and test deployment.
10. Prepare PERSISTENT.
11. Continue rollout: remaining non-prod, then prod.

Show only actions not yet completed.

## 4. Secret Store

Check `/configuration/secret-stores.yml`.

- One store or a single `default_store` - use it.
- Multiple stores - ask one question.
- Store missing - request the type and required field, then create the definition.

Required fields: Vault - `mountPath`, GCP - `projectId`, AWS - `region`, Azure - `vaultName`.
The identifier must match `[A-Za-z_][A-Za-z0-9_]*`.

Do not request authentication values. Ask only for confirmation that the required CI/CD variables are configured.

## 5. Shared Credentials and Cloud Passport Credentials

Process one active source per run.

1. Find all consumers.
2. Open its Credential file.
3. Convert:
   - `usernamePassword` → `type: external` and `properties: username, password`;
   - `secret` → `type: external` without `properties`.
4. Remove all `data`.
5. Do not add `create` for existing Credentials.
6. Add the selected `secretStore`.
7. Leave built-in references as a string `credId`.

### remoteRefPath

For Shared and Cloud Passport, the documentation does not define a common default.

1. Keep the existing path if it is already present.
2. Otherwise use a previously confirmed path for this source.
3. If no path exists, request one common `remoteRefPath` for the entire file.
4. As examples, show: Cloud Passport - `<cluster>`, Shared - `shared/integration`.
5. Do not append `credId` to the end of the path.

For Vault, the final path is: `<remoteRefPath>/<credId>`.

### Validation for Secret Store

- Vault: final path - only `a-zA-Z0-9-/_`.
- Azure: `credId` - `a-zA-Z0-9-`, no more than 32 characters.
- AWS: final name - `a-zA-Z0-9-/_+=.@!`, `credId` no more than 32 characters.
- GCP: `credId` - `a-zA-Z0-9_-`, no more than 32 characters.

Do not rename `credId` automatically. On error, request a new name and note that references must also be updated.

After the change, show only the file, Credential count, `secretStore`, `remoteRefPath`, and consumers.

## 6. Check matching credId values

Compare active sources:

1. Credential Template - from the Template report or after TEMPORARY;
2. Cloud Passport Credentials;
3. Shared Credentials.

Merge priority from bottom to top:

```text
Credential Template
Cloud Passport Credentials
Shared Credentials
```

Check differences in structure, `secretStore`, `remoteRefPath`, and local/external type.

If the result is unambiguous and definitions are compatible, continue without a question. If structure, path, or expected source differ, ask one question only for the conflicting `credId`.

After TEMPORARY, repeat the check against generated `Credentials/credentials.yml`.

## 7. System Credentials

Show found System Credential files and suggest:

1. migrate now;
2. migrate in a separate phase.

Rules:

- do not add to the Environment Credential Template;
- do not include in Environment Credentials homogeneity checks;
- use only Vault or GCP;
- do not add `create: true`;
- specify an explicit `remoteRefPath`;
- the secret must exist in the external store.

If `app-deployer` is selected, prepare it before test deployment. Check matching `credId` values within System Credentials separately.

## 8. TEMPORARY readiness

Check:

- target confirmed as non-prod;
- `Template migration status: VERIFIED`;
- concrete Template version obtained and is not `SNAPSHOT`;
- Credential Template external;
- active Cloud Passport fully external or not used;
- all active Shared Credentials fully external or not used;
- matching `credId` values checked;
- user confirmed secrets exist at expected paths;
- Environment Instance will not mix local and external Credentials;
- `CMDB_IMPORT=false` is used.

If `app-deployer` is included, it must be ready before deployment.

## 9. TEMPORARY, deployment, and PERSISTENT

Never run a pipeline or deployment.

### TEMPORARY

Prepare:

```text
ENV_TEMPLATE_VERSION=<artifactId>:<concrete-version>
ENV_TEMPLATE_VERSION_UPDATE_MODE=TEMPORARY
ENV_NAMES=<cluster>/<environment>
ENV_BUILDER=true
GENERATE_EFFECTIVE_SET=true
CMDB_IMPORT=false
```

Write:

```text
Run the TEMPORARY pipeline manually with the parameters above.
After completion, report the result or provide a link to the pipeline.
```

After execution, check:

- pipeline succeeded;
- generated `Credentials/credentials.yml` contains only `type: external`, with no `data`;
- expected `credId` values are present, no unexpected ones;
- all `secretStore` values exist;
- Effective Set and External Credential Context are formed;
- deployment, pipeline, and topology contexts contain VALS or ESO references, not plaintext;
- `credRef` is absent from `technicalConfigurationParameters`.

Ask the user to perform a test deployment manually. On error, do not prepare PERSISTENT. Suggest fixing the configuration and repeating TEMPORARY and deployment.

### PERSISTENT

After successful deployment, prepare:

```text
ENV_TEMPLATE_VERSION=<artifactId>:<same concrete-version>
ENV_TEMPLATE_VERSION_UPDATE_MODE=PERSISTENT
ENV_NAMES=<cluster>/<environment>
ENV_BUILDER=true
GENERATE_EFFECTIVE_SET=true
CMDB_IMPORT=false
```

After manual PERSISTENT, suggest the next non-prod group. Prod comes last.

## Unbound resources

Check only on command:

```text
Check unbound Shared Credentials and Cloud Passports.
```

For each resource, ask the user to choose:

1. include - the user specifies Environment Instances, binding is added in a separate change;
2. do not include;
3. check later.

Do not include a resource automatically.

## Report

Create or update `external-credentials-migration-report.md`:

```markdown
# External Credentials Migration

## Selected group
- Environment:
- Type:
- Template:
- Template migration status: NOT_VERIFIED | VERIFIED
- Concrete Template version:
- Secret Store:
- Cloud Passport:
- Shared Credentials:
- System Credentials:

## Progress
- [ ] Environment Instances analysed
- [ ] First non-prod selected
- [ ] Template updated and concrete version obtained
- [ ] Secret Store checked
- [ ] Secret presence confirmed
- [ ] Shared Credentials updated
- [ ] Cloud Passport Credentials updated
- [ ] Matching credId values checked
- [ ] System Credentials decision made
- [ ] TEMPORARY parameters prepared
- [ ] TEMPORARY completed by user
- [ ] Generated result checked
- [ ] Test deployment completed by user
- [ ] PERSISTENT parameters prepared
- [ ] PERSISTENT completed by user

## Decision needed
...

## Next action
...
```

Add `Decision needed` only when a question exists. Do not add a full Credential inventory, Credential values, or internal status codes.
