# Configure Local Credentials

- [Configure Local Credentials](#configure-local-credentials)
  - [Overview](#overview)
  - [When to use this guide](#when-to-use-this-guide)
  - [Prerequisites](#prerequisites)
  - [Where credentials come from](#where-credentials-come-from)
  - [Steps](#steps)
    - [Step 1: Set the credentials the template needs](#step-1-set-the-credentials-the-template-needs)
    - [Step 2: Add your own credentials](#step-2-add-your-own-credentials)
    - [Step 3: Pass the credentials files](#step-3-pass-the-credentials-files)
    - [Step 4: Rebuild and verify](#step-4-rebuild-and-verify)
  - [Update credentials later](#update-credentials-later)
  - [Related documentation](#related-documentation)

## Overview

Use this guide to set the credentials of an environment when they are stored in the Instance repository. At the
end, every credential of the environment has a real value.

To keep the values encrypted in Git, enable credential encryption, see
[Credential Encryption](/docs/how-to/credential-encryption.md).

## When to use this guide

Use this guide when the site has no Secret Store. If it has one, use
[Configure External Credentials](/docs/how-to/configure-external-credentials.md) instead. An environment uses one
approach, never both.

## Prerequisites

- The environment exists: its `env_definition.yml` is in the Instance repository, see
  [Create an Environment Inventory](/docs/how-to/create-environment-inventory.md). Create it without credentials
  first. You add them in Step 3.

## Where credentials come from

| File                                                                                        | What it holds                                                          | Who writes it |
|---------------------------------------------------------------------------------------------|------------------------------------------------------------------------|---------------|
| `environments/<cluster>/cloud-passport/<passport-name>-creds.yml`                           | credentials of the Cloud Passport, such as the deploy token and DBaaS  | you           |
| Shared Credentials files in `credentials/` at the environment, cluster, or repository level | all other credentials of the environment                               | you           |
| `environments/<cluster>/<env>/Credentials/credentials.yml`                                  | every credential of the environment, collected from the files above    | EnvGene       |

EnvGene copies every entry of the Shared Credentials files listed in `envTemplate.sharedMasterCredentialFiles` into
`Credentials/credentials.yml`, whether the template references it or not. Do not edit `Credentials/credentials.yml`:
each generation writes it again.

## Steps

### Step 1: Set the credentials the template needs

To find which credentials the template needs:

1. Run the Instance pipeline with `ENV_NAMES: <cluster>/<env>` and `ENV_BUILDER: true`.
2. Open `environments/<cluster>/<env>/Credentials/credentials.yml`. Every credential the template references is
   listed there. A credential without a value holds the placeholder `envgeneNullValue`:

    ```yaml
    dbaas-cluster-dba-cred:
      type: usernamePassword
      data:
        username: envgeneNullValue
        password: envgeneNullValue
    integration-cred:
      type: secret
      data:
        secret: envgeneNullValue
    ```

3. Put the values of the passport credentials in the credentials file next to the passport:

    ```yaml
    # environments/cluster-01/cloud-passport/passport-creds.yml
    dbaas-cluster-dba-cred:
      type: usernamePassword
      data:
        username: dbaas-username
        password: dbaas-password
    ```

4. Put all other values in a Shared Credentials file:

    ```yaml
    # environments/cluster-01/env-01/Inventory/credentials/env-01-creds.yml
    integration-cred:
      type: secret
      data:
        secret: integration-token
    ```

### Step 2: Add your own credentials

A credential the template does not know about, such as the credentials of a partner integration, works the same way.

1. Add it to a Shared Credentials file:

    ```yaml
    # environments/cluster-01/env-01/Inventory/credentials/env-01-creds.yml
    partner-api-cred:
      type: usernamePassword
      data:
        username: partner-username
        password: partner-password
    ```

2. Reference it from an Environment Specific ParameterSet:

    ```yaml
    # environments/cluster-01/env-01/Inventory/parameters/partner-integration.yml
    name: partner-integration
    version: 1
    parameters:
      PARTNER_API_USER: ${creds.get("partner-api-cred").username}
      PARTNER_API_PASSWORD: ${creds.get("partner-api-cred").password}
    ```

3. Bind the ParameterSet in `env_definition.yml`, see
   [Override Template Parameters](/docs/how-to/environment-specific-parameters.md).

Without step 2, the credential reaches `Credentials/credentials.yml` but no parameter uses it.

### Step 3: Pass the credentials files

Pass the Shared Credentials file in one of two ways.

- **Through the Instance pipeline.** Pass the values in the `credentials` block of `ENV_INVENTORY_CONTENT`, and the
  filename in `envTemplate.sharedMasterCredentialFiles`:

    ```json
    "credentials": [
      {
        "action": "create_or_replace",
        "place": "env",
        "name": "env-01-creds",
        "content": {
          "integration-cred": {
            "type": "secret",
            "data": { "secret": "integration-token" }
          }
        }
      }
    ]
    ```

    The values pass through the pipeline parameter in plain text, so restrict who can see the pipeline runs. With
    credential encryption enabled, the pipeline encrypts the file in the same run.

- **By hand.** Commit the file, and add its name, without `.yml`, to `envTemplate.sharedMasterCredentialFiles` in
  `env_definition.yml`.

`place` sets the level of the file: `env`, `cluster`, or `site` for the whole repository. See
[Choose the level of each file](/docs/how-to/create-environment-inventory.md#choose-the-level-of-each-file).

Commit the passport credentials file from Step 1 by hand.

### Step 4: Rebuild and verify

1. Run the Instance pipeline with `ENV_BUILDER: true` and `GENERATE_EFFECTIVE_SET: true`.
2. `Credentials/credentials.yml` holds no `envgeneNullValue`.

If a placeholder remains, the Effective Set generation fails with:

```text
Error while validating credentials:
  credId: <credId> - <field> is not set
```

Set the value of that `credId` as in Step 1. For details, see
[Working with envgeneNullValue](/docs/tutorials/envgene-null-value.md).

## Update credentials later

| What changes                     | How                                                                                                                                         |
|----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| A Cloud Passport credential      | Edit `<passport-name>-creds.yml`, or run Cloud Passport discovery again                                                                     |
| A Shared Credentials file        | Run the pipeline again with the same `credentials` entry, or edit the file. The pipeline replaces the whole file, so pass every credential  |
| One value used in several places | Use [Credential Rotation](/docs/features/cred-rotation.md). SOPS encryption only                                                            |

Then run the pipeline with `ENV_BUILDER: true` and `GENERATE_EFFECTIVE_SET: true`.

## Related documentation

- [Credential Encryption](/docs/how-to/credential-encryption.md)
- [Configure External Credentials](/docs/how-to/configure-external-credentials.md)
- [Create an Environment Inventory](/docs/how-to/create-environment-inventory.md)
- [Override Template Parameters](/docs/how-to/environment-specific-parameters.md)
- [Working with envgeneNullValue](/docs/tutorials/envgene-null-value.md)
- [Credential Rotation](/docs/features/cred-rotation.md)
