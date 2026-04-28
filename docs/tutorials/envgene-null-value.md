# Working with envgeneNullValue

- [Working with envgeneNullValue](#working-with-envgenenullvalue)
  - [What You Will Learn](#what-you-will-learn)
  - [Prerequisites](#prerequisites)
  - [Overview](#overview)
  - [Where validation happens](#where-validation-happens)
  - [Scenario 1: Mandatory parameters in templates](#scenario-1-mandatory-parameters-in-templates)
    - [Problem (mandatory parameters)](#problem-mandatory-parameters)
    - [Example in template (ParameterSet)](#example-in-template-parameterset)
    - [How to resolve](#how-to-resolve)
    - [Key point](#key-point)
  - [Where to put parameter overrides](#where-to-put-parameter-overrides)
  - [Scenario 2: Credentials placeholder](#scenario-2-credentials-placeholder)
    - [Problem (credentials)](#problem-credentials)
  - [Credential Type 1: usernamePassword](#credential-type-1-usernamepassword)
    - [Generated `credentials.yml` (username/password)](#generated-credentialsyml-usernamepassword)
  - [Credential Type 2: secret](#credential-type-2-secret)
    - [Generated `credentials.yml` (secret)](#generated-credentialsyml-secret)
  - [How to Resolve Credentials](#how-to-resolve-credentials)
    - [Option 1: Cloud Passport](#option-1-cloud-passport)
    - [Option 2: Shared Credentials](#option-2-shared-credentials)
      - [usernamePassword example](#usernamepassword-example)
      - [secret example](#secret-example)
  - [Verification Step (Required)](#verification-step-required)
  - [Before / After Example](#before--after-example)
  - [Summary](#summary)

## What You Will Learn

By the end of this tutorial you will understand:

- What `envgeneNullValue` represents
- Why EnvGene uses it
- Two practical scenarios where it appears:
  - Mandatory template parameters
  - Credentials placeholders for `usernamePassword` and `secret` types

## Prerequisites

- A working EnvGene setup (Template Repository + Instance Repository)
- Basic understanding of environment generation

## Overview

`envgeneNullValue` is a special placeholder used by EnvGene to represent **missing or unresolved values**.

It is intentionally used to:

- Mark values that must be provided later
- Prevent incomplete or insecure deployments

Common use cases:

- Mandatory template parameters
- Credentials placeholders

If a required value remains `envgeneNullValue` where a real value is mandatory, validation fails and deployment is blocked.

## Where validation happens

EnvGene validates that no `envgeneNullValue` placeholders remain before they reach a target system. The validation runs at two pipeline stages and covers both credentials and parameters:

- **`generate_effective_set`** — validates the data that goes into the Effective Set.
- **`cmdb_import`** — validates the data that is about to be pushed to the CMDB.

At each stage the same two scopes are checked, and both stages emit identical log messages on failure:

- **Parameters:** every value in `deployParameters`, `e2eParameters`, and `technicalConfigurationParameters` is checked. If any value equals `envgeneNullValue`, the job aborts with:

  ```text
  Error while validating parameters:
    <entity>.<paramType>.<key> - is not set
  ```

  Where `<entity>` is the Cloud or Namespace name, `<paramType>` is `deployParameters`, `e2eParameters`, or `technicalConfigurationParameters`, and `<key>` is the parameter key.

- **Credentials:** for every entry in the Environment's `Credentials/credentials.yml`, the secret material is checked — for `usernamePassword`: `username` and `password`; for `secret`: `secret`; for `vault`: `secretId`. If any value equals `envgeneNullValue`, the job aborts with:

  ```text
  Error while validating credentials:
    credId: <credId> - <field> is not set
  ```

  Where `<credId>` is the credential identifier and `<field>` is the unresolved field (`username or password`, `secret`, or `secretId`).

A failure at either stage blocks deployment until the placeholders are replaced with real values.

## Scenario 1: Mandatory parameters in templates

### Problem (mandatory parameters)

Some template values cannot be decided at template-authoring time because they depend on the target environment. To make the requirement explicit, templates set such parameters to `envgeneNullValue`.

### Example in template (ParameterSet)

```yaml
name: api-config
parameters:
  API_URL: envgeneNullValue
```

This signals that the value is required and must be provided by the Instance repository (environment-level override).

If the value is not provided, the parameter remains `envgeneNullValue` and the pipeline fails as described in [Where validation happens](#where-validation-happens).

### How to resolve

Provide the value via an Environment-Specific ParameterSet in the Instance repository, for example:

```yaml
name: api-config
parameters:
  API_URL: "https://api.dev.example.com"
```

See [Where to put parameter overrides](#where-to-put-parameter-overrides) for the file location and how to wire the ParameterSet into the Environment.

### Key point

- Templates remain reusable
- Environments supply environment-specific values
- Missing values are explicitly detected and rejected

## Where to put parameter overrides

To resolve `envgeneNullValue` for a template parameter, override it via an Environment-Specific
ParameterSet in the Instance repository. The override is a two-step process:

1. Create a ParameterSet file with the same `name` as the one defined in the template, placing the real value
   under `parameters`. The file is located at one of the following paths (in priority order, highest first):

   - `/environments/<cluster-name>/<environment-name>/Inventory/parameters/<paramset-name>.yml` — environment-specific
   - `/environments/<cluster-name>/parameters/<paramset-name>.yml` — cluster-wide
   - `/environments/parameters/<paramset-name>.yml` — global

2. Wire the ParameterSet into the Environment via `env_definition.yml` using the field that matches the
   parameter purpose:

   - `envTemplate.envSpecificParamsets` — for deployment parameters (`deployParameters`)
   - `envTemplate.envSpecificE2EParamsets` — for pipeline (e2e) parameters (`e2eParameters`)
   - `envTemplate.envSpecificTechnicalParamsets` — for technical/runtime parameters (`technicalConfigurationParameters`)

Each entry maps an association key to the list of ParameterSet names to apply. The key is:

- The literal `cloud` — to associate the override with the Cloud
- A Namespace identifier — to associate with a specific Namespace (the identifier is defined by `deploy_postfix`
  in the Template Descriptor, or by the Namespace template filename without extension)

Example — overriding `API_URL` (defined in the template ParameterSet `api-config`) at the Cloud level:

```yaml
# /environments/cluster-1/dev01/Inventory/parameters/api-config.yml
name: api-config
parameters:
  API_URL: "https://api.dev.example.com"
```

```yaml
# /environments/cluster-1/dev01/Inventory/env_definition.yml
envTemplate:
  envSpecificParamsets:
    cloud:
      - api-config
```

For full details on Environment-Specific ParameterSets — locations, lookup order, and merge behavior — see
[Environment-Specific ParameterSet](/docs/envgene-objects.md#environment-specific-parameterset).

## Scenario 2: Credentials placeholder

### Problem (credentials)

When EnvGene generates a `credentials.yml` file (for example from Cloud Passport),
it may not have access to actual secret values.

Instead, it generates placeholders using `envgeneNullValue`.

## Credential Type 1: usernamePassword

### Generated `credentials.yml` (username/password)

```yaml
dbaas-cluster-dba-cred:
  type: usernamePassword
  data:
    username: "envgeneNullValue" # FillMe
    password: "envgeneNullValue" # FillMe
```

If `username` or `password` is not resolved, the pipeline fails as described in [Where validation happens](#where-validation-happens).

## Credential Type 2: secret

### Generated `credentials.yml` (secret)

```yaml
consul-admin-cred:
  type: secret
  data:
    secret: "envgeneNullValue" # FillMe
```

If the `secret` is not resolved, the pipeline fails as described in [Where validation happens](#where-validation-happens).

## How to Resolve Credentials

`envgeneNullValue` must be replaced before deployment using one of the supported methods.

### Option 1: Cloud Passport

Provide credential values via Cloud Passport configuration.

### Option 2: Shared Credentials

See [Shared Credentials File](/docs/envgene-objects.md#shared-credentials-file) in `envgene-objects.md` for locations and merge behavior.

#### usernamePassword example

```yaml
dbaas-cluster-dba-cred:
  type: usernamePassword
  data:
    username: "real_user"
    password: "secure_password"
```

#### secret example

```yaml
consul-admin-cred:
  type: secret
  data:
    secret: "secret-123"
```

## Verification Step (Required)

Before deployment, ensure no placeholders remain.

PowerShell example:

```powershell
Get-ChildItem -Recurse -Include *.yml,*.yaml |
  Select-String -Pattern 'envgeneNullValue'
```

If any matches are found:

- Do **not** proceed with deployment

## Before / After Example

**Before resolution** (same structure as the generated `credentials.yml` examples above):

```yaml
dbaas-cluster-dba-cred:
  type: usernamePassword
  data:
    username: "envgeneNullValue" # FillMe
    password: "envgeneNullValue" # FillMe

consul-admin-cred:
  type: secret
  data:
    secret: "envgeneNullValue" # FillMe
```

**After resolution:**

```yaml
dbaas-cluster-dba-cred:
  type: usernamePassword
  data:
    username: "prod_user"
    password: "secure_password"

consul-admin-cred:
  type: secret
  data:
    secret: "secret-123"
```

## Summary

- `envgeneNullValue` is an intentional placeholder used to mark missing or unresolved values.
- It appears in both mandatory template parameters and generated credentials.
- It prevents incomplete or insecure deployments by failing validation until values are provided.
- Always resolve `envgeneNullValue` before deployment.
