---
name: envgene-external-credentials-validator
description: Validate the current EnvGene External Credentials migration step: Template or Instance Repository changes, TEMPORARY readiness, generated result, test deployment, or PERSISTENT. Update the report and suggest one next action.
---

# EnvGene External Credentials Validator

Validate only the step the user requested or the step marked next in `external-credentials-migration-report.md`.

## Constraints

- Work only with the local repository and user data.
- Do not use the web, GitHub, remote documentation, or helper scripts.
- Never run a pipeline, deployment, TEMPORARY, PERSISTENT, commit, push, or merge.
- Do not output Credential values.
- Do not edit generated files.

## Template Repository

Check:

- one Credential Template for the selected Environment Template;
- Descriptor contains `external_credential_template`;
- all entries are `type: external`, with no `data`, values, or `create` for existing Credentials;
- username/password have `properties: username, password`;
- single-value entries have no `properties`;
- structure is determined from references, not from the `credId` name;
- not all Credentials are assigned the same `properties` without confirmation;
- Cloud Passport and Shared Credentials are not duplicated unnecessarily;
- local references replaced only in `deployParameters` and `e2eParameters`;
- built-in references remain strings;
- `credRef` is absent from `technicalConfigurationParameters`;
- `credRef.property` matches `properties`;
- `credRef` without `property` points to a Credential without `properties`;
- every used `credId` has a source.

Validate `credId` against Secret Store type:

- Vault: final path - `a-zA-Z0-9-/_`;
- Azure: `credId` - `a-zA-Z0-9-`, up to 32 characters;
- AWS: final name - `a-zA-Z0-9-/_+=.@!`, `credId` up to 32 characters;
- GCP: `credId` - `a-zA-Z0-9_-`, up to 32 characters.

If `remoteRefPath` is not specified, use `{{ current_env.cloud }}/{{ current_env.name }}`. Do not rename `credId` automatically.

## Instance Repository

Check:

- `/configuration/secret-stores.yml` and required fields;
- active Shared and Cloud Passport Credentials have `type: external`;
- `data` removed;
- `properties` structure is correct;
- `create` not added for existing Credentials;
- `secretStore` exists;
- `remoteRefPath` confirmed and does not contain a repeatedly appended `credId`;
- all consumers of shared sources are accounted for;
- generated `Credentials/credentials.yml` was not edited manually.

Compare `credId` values between Credential Template, Cloud Passport, and Shared Credentials. Account for priority:

```text
Credential Template
Cloud Passport Credentials
Shared Credentials
```

Show an issue only when structure, `secretStore`, `remoteRefPath`, or expected source differ.

Check System Credentials separately: Vault or GCP only, no `create: true`, with explicit `remoteRefPath`. Do not include them in Environment Credentials homogeneity.

## TEMPORARY readiness

Check:

- target confirmed as non-prod;
- `Template migration status: VERIFIED`;
- concrete Template version is not `SNAPSHOT`;
- Credential Template external;
- active Cloud Passport and Shared Credentials fully external or not used;
- matching `credId` values checked;
- secret presence in the external store confirmed by the user;
- local and external Credentials are not mixed;
- `CMDB_IMPORT=false` is used.

If `app-deployer` is included, it must be ready before deployment.

After validation, prepare TEMPORARY parameters, but do not run the pipeline.

## TEMPORARY and generated result

From the user result or link, check:

- pipeline succeeded and Template applied temporarily;
- generated `Credentials/credentials.yml` contains only `type: external`, with no `data`;
- expected `credId` values are present, no unexpected ones;
- merge follows source priority;
- all `secretStore` values exist;
- Effective Set and External Credential Context are formed;
- deployment, pipeline, and topology contexts contain VALS or ESO references, not plaintext;
- with `SECRET_FLOW=external-values`, the application has `eso_support=true`;
- `credRef` is absent from `technicalConfigurationParameters`.

Do not output the full generated file if values are found in it.

## Deployment and PERSISTENT

Ask the user to perform a test deployment manually.

On error, do not prepare PERSISTENT. Show the cause, suggest fixing the configuration or preparing the missing secret, then repeat TEMPORARY and deployment.

Prepare PERSISTENT only after successful repository checks, TEMPORARY, generated result, and deployment. Use the same concrete Template version and `CMDB_IMPORT=false`.

After manual PERSISTENT, check that `envTemplate.artifact` contains the new concrete version.

## Report

Update the checklist and add:

```markdown
## Latest check
- Checked:
- Result: success | action required | error
- To fix:

## Next action
...
```

Show only critical notes and one next action.
