# Working with envgeneNullValue

- [Working with envgeneNullValue](#working-with-envgenenullvalue)
  - [What You Will Learn](#what-you-will-learn)
  - [Prerequisites](#prerequisites)
  - [Overview](#overview)
  - [Scenario: Credentials Placeholder](#scenario-credentials-placeholder)
    - [Problem](#problem)
  - [Credential Type 1: usernamePassword](#credential-type-1-usernamepassword)
    - [Generated `credentials.yml` (username/password)](#generated-credentialsyml-usernamepassword)
    - [Behavior When Values Are Missing](#behavior-when-values-are-missing)
  - [Credential Type 2: secret](#credential-type-2-secret)
    - [Generated `credentials.yml` (secret)](#generated-credentialsyml-secret)
    - [Behavior When Value Is Missing](#behavior-when-value-is-missing)
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

- What `envgeneNullValue` is
- Why EnvGene uses it
- A **practical scenario: credentials placeholder** covering:

  - `usernamePassword` credentials
  - `secret` credentials

## Prerequisites

- A working EnvGene setup (Template Repository + Instance Repository)
- Basic understanding of environment generation

## Overview

`envgeneNullValue` is a special placeholder used by EnvGene to represent **missing or unresolved values**.

It is intentionally used to:

- Mark values that must be provided later
- Prevent incomplete or insecure deployments

Common use case:

If a required value remains `envgeneNullValue` where a real value is mandatory, validation fails and deployment is blocked.

## Scenario: Credentials Placeholder

### Problem

When EnvGene fills the [Environment Credentials File](/docs/envgene-objects.md#environment-credentials-file) (`Credentials/credentials.yml`),
it not have access to actual secret values.

Instead, credential fields can be set to `envgeneNullValue` until you resolve them.

## Credential Type 1: usernamePassword

### Generated `credentials.yml` (username/password)

```yaml
dbaas-cluster-dba-cred:
  type: "usernamePassword"
  data:
    username: "envgeneNullValue" # FillMe
    password: "envgeneNullValue" # FillMe
```

### Behavior When Values Are Missing

If credentials are not resolved:

- Validation fails during environment generation
- Deployment is blocked

Example error:

```text
envgenehelper.errors.ValidationError: Error while validating credentials:
 credId: dbaas-cluster-dba-cred - username or password is not set
```

## Credential Type 2: secret

### Generated `credentials.yml` (secret)

```yaml
consul-admin-cred:
  type: "secret"
  data:
    secret: "envgeneNullValue" # FillMe
```

### Behavior When Value Is Missing

If the secret is not resolved:

- Validation fails during environment generation
- Deployment is blocked

Example error:

```text
Error while validating credentials:
  credId: consul-admin-cred - secret is not set
```

## How to Resolve Credentials

`envgeneNullValue` must be replaced before deployment using one of the supported methods.

### Option 1: Cloud Passport

Provide credential values via Cloud Passport configuration.

### Option 2: Shared Credentials

See [Shared Credentials File](/docs/envgene-objects.md#shared-credentials-file) in `envgene-objects.md` for locations and merge behavior.

#### usernamePassword example

```yaml
dbaas-cluster-dba-cred:
  type: "usernamePassword"
  data:
    username: "real_user"
    password: "secure_password"
```

#### secret example

```yaml
consul-admin-cred:
  type: "secret"
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
  type: "usernamePassword"
  data:
    username: "envgeneNullValue" # FillMe
    password: "envgeneNullValue" # FillMe

consul-admin-cred:
  type: "secret"
  data:
    secret: "envgeneNullValue" # FillMe
```

**After resolution:**

```yaml
dbaas-cluster-dba-cred:
  type: "usernamePassword"
  data:
    username: "prod_user"
    password: "secure_password"

consul-admin-cred:
  type: "secret"
  data:
    secret: "secret-123"
```

## Summary

- `envgeneNullValue` is an **intentional placeholder**
- Used in **credentials generation** for:

  - `usernamePassword`
  - `secret` types

- Prevents incomplete or insecure deployments when validation requires real values
- Must be replaced with real values before deployment wherever your pipeline enforces it
