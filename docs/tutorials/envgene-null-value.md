# Working with envgeneNullValue

- [Working with envgeneNullValue](#working-with-envgenenullvalue)
  - [What You Will Learn](#what-you-will-learn)
  - [Prerequisites](#prerequisites)
  - [Overview](#overview)
  - [Scenario 1: Mandatory parameters in templates](#scenario-1-mandatory-parameters-in-templates)
    - [Problem (mandatory parameters)](#problem-mandatory-parameters)
    - [Example in template (ParameterSet)](#example-in-template-parameterset)
    - [Behavior when not overridden](#behavior-when-not-overridden)
    - [How to resolve](#how-to-resolve)
    - [Key point](#key-point)
  - [Where to put parameter overrides](#where-to-put-parameter-overrides)
  - [Scenario 2: Credentials placeholder](#scenario-2-credentials-placeholder)
    - [Problem (credentials)](#problem-credentials)
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

- What `envgeneNullValue` represents
- Why EnvGene uses it
- **two practical scenarios** where it appears:
  - mandatory template parameters
  - credentials placeholders for `usernamePassword` and `secret` types

## Prerequisites

- A working EnvGene setup (Template Repository + Instance Repository)
- Basic understanding of environment generation

## Overview

`envgeneNullValue` is a special placeholder used by EnvGene to represent **missing or unresolved values**.

It is intentionally used to:

- Mark values that must be provided later
- Prevent incomplete or insecure deployments

Common use case:

- **mandatory template parameters**
- **Credentials placeholder**

If a value remains `envgeneNullValue`, validation will fail and deployment will be blocked.

## Scenario 1: Mandatory parameters in templates

### Problem (mandatory parameters)

Some template values cannot be decided at template-authoring time because they depend on the target environment. To make the requirement explicit, templates set such parameters to `envgeneNullValue`.

---

### Example in template (ParameterSet)

```yaml
API_URL: envgeneNullValue
```

This signals that the value is required and must be provided by the instance repository (environment-level override).

---

### Behavior when not overridden

If the value is not provided during environment generation:

- the parameter remains `envgeneNullValue`
- validation fails
- deployment is blocked

---

### How to resolve

Provide the value in the instance repository, for example:

```yaml
API_URL: https://api.dev.example.com
```

You can supply this via environment-specific parameter files or overrides in the instance repository.

---

### Key point

- templates remain reusable
- environments supply environment-specific values
- missing values are explicitly detected and rejected

---

## Where to put parameter overrides

When you resolve `envgeneNullValue` for template parameters, place the values in the instance repository under one of the following top-level sections depending on their purpose:

- `deployParameters`
- `e2eParameters`
- `technicalConfigurationParameters`

Keep an empty mapping if you have no values for a section in a given environment (that's valid). Example:

```yaml
deployParameters:
  API_URL: "https://api.dev.example.com"

e2eParameters: {}

technicalConfigurationParameters:
  max_retries: 5
```

Place required keys (the ones set to `envgeneNullValue` in templates) under the appropriate section so validation can succeed.

---

## Scenario 2: Credentials placeholder

### Problem (credentials)

When EnvGene generates a `credentials.yml` file (for example from Cloud Passport),
it may not have access to actual secret values.

Instead, it generates placeholders using `envgeneNullValue`.

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

**Before resolution:**

```yaml
username: envgeneNullValue
password: envgeneNullValue
secret: envgeneNullValue
```

**After resolution:**

```yaml
username: prod_user
password: secure_password
secret: secret-123
```

## Summary

- `envgeneNullValue` is an intentional placeholder used to mark missing or unresolved values.
- It appears in both mandatory template parameters and generated credentials.
- It prevents incomplete or insecure deployments by failing validation until values are provided.
- Always resolve `envgeneNullValue` before deployment.