# Configure external Credentials

- [Configure external Credentials](#configure-external-credentials)
  - [Overview](#overview)
  - [When to use external Credentials](#when-to-use-external-credentials)
  - [Prerequisites](#prerequisites)
  - [Set a sensitive parameter](#set-a-sensitive-parameter)
    - [Step 1: Reference a credential in the parameter](#step-1-reference-a-credential-in-the-parameter)
    - [Step 2: Describe the credential in a Credential Template](#step-2-describe-the-credential-in-a-credential-template)
    - [Step 3: Publish the template](#step-3-publish-the-template)
    - [Step 4: Switch the environment to the new template version](#step-4-switch-the-environment-to-the-new-template-version)
    - [Step 5: Build the environment](#step-5-build-the-environment)
    - [Step 6: Set the value](#step-6-set-the-value)
    - [Verify the result](#verify-the-result)
  - [Use one value in several environments](#use-one-value-in-several-environments)
  - [Related documentation](#related-documentation)

## Overview

A parameter can hold a sensitive value, such as a password or a token. Set such a parameter through an external
Credential: the parameter references the Credential by its ID, and the value lives in a Secret Store. The Instance
repository and the deployment hold only references to the value. How EnvGene collects and generates Credentials is
described in [Credential processing](/docs/features/credential-processing.md).

For a complete file set, see the [external credentials samples](/docs/samples/external-credentials/).

## When to use external Credentials

Use external Credentials when the site has a Secret Store. If it has none, use
[Configure local Credentials](/docs/how-to/configure-local-credentials.md) instead. If the environment already keeps
local Credentials, migrate them, see
[Migrate an instance repository to external Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md).

> [!IMPORTANT]
> A Secret Store switches all environments of the Instance repository to external Credentials. Every Credential of
> these environments must then be external, including the Cloud Passport credentials and the Shared Credentials, in
> the format from [Step 2](#step-2-describe-the-credential-in-a-credential-template).

## Prerequisites

- The Environment Template exists, see [Create a simple template](/docs/how-to/create-simple-template.md).
- The Instance repository has a Secret Store configured, see
  [Configure a Secret Store](/docs/how-to/configure-secret-store.md).
- The environment does not use CMDB import. CMDB import is not supported for external Credentials.
- To put values from outside into the Secret Store, you have the
  [External Credentials provisioning CLI](/modules/external-cred-provision/README.md) installed and access to the
  Secret Store from your machine.

## Set a sensitive parameter

### Step 1: Reference a credential in the parameter

In the Template repository, set the value of the parameter to a credential reference. Do it in `deployParameters`
or `e2eParameters` of the Cloud, Namespace, and Tenant templates, or in their ParameterSets:

```yaml
# templates/parameters/partner-integration.yml
name: partner-integration
version: 1
parameters:
  PARTNER_API_USER:
    $type: credRef
    credId: partner-api-cred
    property: username
  PARTNER_API_PASSWORD:
    $type: credRef
    credId: partner-api-cred
    property: password
  APP_DB_PASSWORD:
    $type: credRef
    credId: app-db-password
```

- Choose the credential ID yourself. It must be unique in the environment. Several parameters can use one ID.
- `property: username` and `property: password` read one field of a username and password pair. Without
  `property`, the reference reads one value.

A template can still hold `${creds.get(...)}` macros, such as a parent template from another repository. EnvGene
rewrites them to `$type: credRef` when it generates the Environment Instance, so you do not need to change them.

### Step 2: Describe the credential in a Credential Template

1. In the Template repository, create the folder `templates/env_templates/external-cred/`.
2. In this folder, create a Credential Template file for the Environment Template, for example
   `<template-name>.yml.j2`. Each Environment Template points to its own Credential Template, so the folder can hold
   several files.
3. In the Template Descriptor of the Environment Template, add `external_credential_template` with the path to this
   file:

    ```yaml
    # templates/env_templates/external-cred-sample.yml
    tenant: "{{ templates_dir }}/env_templates/external-cred/tenant.yml.j2"
    cloud: "{{ templates_dir }}/env_templates/external-cred/cloud.yml.j2"
    external_credential_template: "{{ templates_dir }}/env_templates/external-cred/external-credentials.yml.j2"
    namespaces:
      - template_path: "{{ templates_dir }}/env_templates/external-cred/ns.yml.j2"
    ```

4. In the Credential Template, describe:
    - every credential ID from Step 1
    - every credential ID that a [built-in field](/docs/features/external-creds.md#built-in-credential-references)
      holds, such as `credentialsId` of a Namespace or `dbaasConfigs[].credentialsId` of the Cloud, in this template
      and in its parent template. Skip the ones that the Cloud Passport credentials declare

    Choose the fields of each credential:

    | Field           | Value                                                                                                                                                                                                                           |
    |-----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | `type`          | Always `external`                                                                                                                                                                                                               |
    | `secretStore`   | The identifier of the Secret Store from `secret-stores.yml`                                                                                                                                                                     |
    | `remoteRefPath` | The folder in the store, for example `{{ current_env.cluster.name }}/{{ current_env.name }}`. Do not add the credential ID: EnvGene appends it. See [Credential Template](/docs/features/external-creds.md#credential-template) |
    | `create`        | `true` if EnvGene generates the value. Leave it out if the value comes from outside, such as a partner token                                                                                                                    |
    | `properties`    | `- name: username` and `- name: password` for a username and password pair. Leave it out for one value                                                                                                                          |

    ```yaml
    # templates/env_templates/external-cred/<template-name>.yml.j2
    partner-api-cred:           # the value comes from the partner
      type: external
      secretStore: default_store
      remoteRefPath: "{{ current_env.cluster.name }}/{{ current_env.name }}"
      properties:
        - name: username
        - name: password
    app-db-password:            # EnvGene generates the value
      type: external
      create: true
      secretStore: default_store
      remoteRefPath: "{{ current_env.cluster.name }}/{{ current_env.name }}"
    ns-deploy-token:            # held by credentialsId of a Namespace
      type: external
      secretStore: default_store
      remoteRefPath: "{{ current_env.cluster.name }}/{{ current_env.name }}"
    ```

For a complete example, see the sample
[Credential Template](/docs/samples/external-credentials/template-repository/templates/env_templates/external-cred/external-credentials.yml.j2)
and
[Template Descriptor](/docs/samples/external-credentials/template-repository/templates/env_templates/external-cred-sample.yml).

> [!NOTE]
> Do not create a Credential Template for a parent template. EnvGene generates the credentials of its sensitive
> parameters with `secretStore: default_store`, `remoteRefPath: "{{ current_env.cloud }}/{{ current_env.name }}"`,
> and no `create`. A credential read through `property`, or through `.username` or `.password` of a macro, also gets
> both `properties`.

In an Instance repository without a Secret Store, EnvGene ignores the Credential Template. The same template works
for local Credentials.

### Step 3: Publish the template

Run the template build pipeline and publish a new version, for example `project-env-template:2.0.0`.

### Step 4: Switch the environment to the new template version

In the Instance repository, set the template version from Step 3 in `env_definition.yml`:

```yaml
# environments/cluster-01/env-01/Inventory/env_definition.yml
envTemplate:
  artifact: "project-env-template:2.0.0"
```

### Step 5: Build the environment

Run the Instance pipeline:

```yaml
ENV_NAMES: cluster-01/env-01
ENV_BUILDER: true
GENERATE_EFFECTIVE_SET: true
EXTERNAL_CREDENTIAL_PROVISIONING: skip
```

`environments/cluster-01/env-01/Credentials/credentials.yml` now holds the credentials from Step 2, and
`effective-set/external-credential/external-credentials.yaml` of the environment lists their paths in the store.

### Step 6: Set the value

EnvGene generates the values of the credentials with `create: true`. Set the values of the other credentials with the
[External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md):

1. Copy `environments/cluster-01/env-01/effective-set/external-credential/external-credentials.yaml` outside the
   repository. In the copy, for each credential with `strategy: fail_if_absent`, set `strategy: create_if_absent` and
   add `data` with the value:

    ```yaml
    credentials:
      partner-api-cred:
        vals: "ref+vault://secret/cluster-01/env-01/partner-api-cred"
        strategy: create_if_absent
        data:
          username: partner-user
          password: partner-password
    ```

    Keep `vals` as it is: it holds the path in the store. For the shape of `data` for one value, see
    [Input format](/docs/features/external-creds-provisioning-cli.md#input-format).

2. Set the variables from
   [Configure a Secret Store](/docs/how-to/configure-secret-store.md#step-2-give-the-instance-pipeline-access-to-the-secret-store)
   in your shell, and run the CLI:

    ```bash
    external-cred-provision external-credentials.yaml
    ```

3. Delete the copy. It holds the values in plain text.
4. Run the Instance pipeline again without `EXTERNAL_CREDENTIAL_PROVISIONING`. The job checks every secret in the
   store and creates the secrets with `create: true`.

### Verify the result

1. `effective-set/deployment/<namespace>/<application>/values/credentials.yaml` of the environment holds references
   to the Secret Store instead of values.
2. A test deployment of the environment starts, and the applications authenticate to their dependencies.

## Use one value in several environments

The Credential Template from Step 2 puts the secret of each environment under its own path, so each environment needs
its own value. When several environments use the same value, describe the credential once in a Shared Credentials
file with one path for all of them:

1. Create the file at the level of the environments that use it: `environments/<cluster>/credentials/` for one
   cluster, `environments/credentials/` for the whole repository. See
   [Choose the level of each file](/docs/how-to/create-environment-inventory.md#choose-the-level-of-each-file).

    ```yaml
    # environments/cluster-01/credentials/cluster-01-creds.yml
    partner-api-cred:
      type: external
      secretStore: default_store
      remoteRefPath: cluster-01
      properties:
        - name: username
        - name: password
    ```

2. In `env_definition.yml` of each environment, list the filename without `.yml`:

    ```yaml
    envTemplate:
      sharedMasterCredentialFiles:
        - cluster-01-creds
    ```

3. Build the environments as in [Step 5](#step-5-build-the-environment), and set the value once as in
   [Step 6](#step-6-set-the-value).

The Shared Credentials file overrides the description of the same credential ID in the Credential Template.

## Related documentation

- [Configure a Secret Store](/docs/how-to/configure-secret-store.md)
- [Configure local Credentials](/docs/how-to/configure-local-credentials.md)
- [Credential processing](/docs/features/credential-processing.md)
- [External Credentials](/docs/features/external-creds.md)
- [External Credentials provisioning CLI](/docs/features/external-creds-provisioning-cli.md)
- [Migrate an instance repository to external Credentials](/docs/how-to/migrate-instance-repository-to-external-credentials.md)
