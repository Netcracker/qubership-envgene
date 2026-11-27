# Defining and Managing Complex Parameters in EnvGene Using YAML Objects

- [Defining and Managing Complex Parameters in EnvGene Using YAML Objects](#defining-and-managing-complex-parameters-in-envgene-using-yaml-objects)
  - [Overview](#overview)
    - [When to Use This Guide](#when-to-use-this-guide)
    - [Core Rule](#core-rule)
  - [Why YAML Objects Are Required](#why-yaml-objects-are-required)
    - [Structural Integrity](#structural-integrity)
    - [Clean and Meaningful Git Diffs](#clean-and-meaningful-git-diffs)
    - [No Manual Escaping](#no-manual-escaping)
  - [How to Define Complex Parameters Correctly](#how-to-define-complex-parameters-correctly)
    - [Defining a Map (Object)](#defining-a-map-object)
    - [Defining a List](#defining-a-list)
    - [Do not mix secret and non-secret values in one list](#do-not-mix-secret-and-non-secret-values-in-one-list)
  - [How EnvGene Processes Complex Parameters](#how-envgene-processes-complex-parameters)
    - [During Environment Instance Generation](#during-environment-instance-generation)
    - [During CMDB Import](#during-cmdb-import)
  - [End-to-End Example](#end-to-end-example)
    - [YAML Definition in Template or Environment-specific parameters](#yaml-definition-in-template-or-environment-specific-parameters)
    - [Effective Set Output](#effective-set-output)
    - [CMDB Imported Representation](#cmdb-imported-representation)
  - [Design Principles for YAML](#design-principles-for-yaml)
    - [Treat YAML as Structured Data](#treat-yaml-as-structured-data)
    - [Preserve Type Integrity](#preserve-type-integrity)
    - [Avoid Embedded JSON Inside YAML](#avoid-embedded-json-inside-yaml)
  - [Migration Strategy for Existing Multiline or JSON Strings](#migration-strategy-for-existing-multiline-or-json-strings)
  - [Operational Impact](#operational-impact)
  - [Final Recommendation](#final-recommendation)

## Overview

This guide explains how to define complex parameters (maps and lists) in EnvGene using native YAML objects instead of multiline or JSON strings. It is intended for engineers working with Git-managed EnvGene instance or template repositories.

### When to Use This Guide

Use this guide when:

- Defining new parameters in EnvGene
- Refactoring existing multiline string parameters
- Debugging CMDB import formatting issues
- Reviewing pull requests involving complex configuration
- Establishing configuration standards across teams

### Core Rule

> Always define complex parameters as structured YAML objects. Never use multiline strings or JSON strings for structured configuration.

Complex parameters are maps (objects) and lists (arrays). Maps can contain other maps or lists as values.

## Why YAML Objects Are Required

### Structural Integrity

When defined as YAML objects:

- YAML schema validation works
- Linters and IDE tooling function correctly

When defined as multiline strings:

- No validation is applied
- Type safety is broken

### Clean and Meaningful Git Diffs

Structured YAML enables semantic diffs; only the changed keys appear in the diff:

```diff
 deploymentConfig:
   replicas: 2
   strategy:
     type: RollingUpdate
     maxUnavailable: 0
   resources:
     limits:
-      memory: 512Mi
+      memory: 1Gi
       cpu: 500m
     requests:
       memory: 256Mi
       cpu: 250m
```

Escaped JSON in a string shows the entire value as one long line; a single field change (e.g. `memory`) is buried in escaped quotes and hard to review:

```diff
- deploymentConfig: "{ \"replicas\":2,\"strategy\":{\"type\":\"RollingUpdate\",\"maxUnavailable\":0},\"resources\":{\"limits\":{\"memory\":\"512Mi\",\"cpu\":\"500m\"},\"requests\":{\"memory\":\"256Mi\",\"cpu\":\"250m\"}} }"
+ deploymentConfig: "{ \"replicas\":2,\"strategy\":{\"type\":\"RollingUpdate\",\"maxUnavailable\":0},\"resources\":{\"limits\":{\"memory\":\"1Gi\",\"cpu\":\"500m\"},\"requests\":{\"memory\":\"256Mi\",\"cpu\":\"250m\"}} }"
```

Structured YAML improves:

- Code reviews
- Drift detection
- Merge conflict resolution

### No Manual Escaping

Multiline or escaped JSON string (e.g. a small map):

```yaml
config: "{ \"limits\": { \"cpu\": \"500m\" } }"
```

Native YAML:

```yaml
config:
  limits:
    cpu: 500m
```

Manual escaping:

- Is error-prone
- Breaks readability
- Causes CMDB import issues

## How to Define Complex Parameters Correctly

### Defining a Map (Object)

Correct:

```yaml
parameters:
  resourceLimits:
    cpu: 500m
    memory: 1Gi
```

Incorrect (multiline string - map is stored as text):

```yaml
parameters:
  resourceLimits: |
    cpu: 500m
    memory: 1Gi
```

Incorrect (JSON string):

```yaml
parameters:
  resourceLimits: '{"cpu":"500m","memory":"1Gi"}'
```

### Defining a List

Correct:

```yaml
parameters:
  allowedIPs:
    - 10.10.0.1
    - 10.10.0.2
    - 10.10.0.3
```

Incorrect (multiline string - list is stored as text):

```yaml
parameters:
  allowedIPs: |
    - 10.10.0.1
    - 10.10.0.2
```

Incorrect (JSON string):

```yaml
parameters:
  allowedIPs: '["10.10.0.1","10.10.0.2","10.10.0.3"]'
```

### Do not mix secret and non-secret values in one list

A list must not hold both a secret value, written as a `${creds.get(...)}` reference, and a non-secret
value. Keep a list either all-secret or all-non-secret. When entries pair a secret with non-secret data,
model them as a map instead of a list.

EnvGene writes secret and non-secret values to separate files in the effective set, the credentials file
and the parameters file. A list that mixes the two is split across both files under the same key, the
secret entries in one file and the rest in the other. The deployer then layers the two files. It replaces
a list rather than merging it, and merges only maps, key by key. One file's copy of the list survives, the
other is dropped with no error, and the application reads a half-built value.

Not OK - each entry pairs a secret `token` with a non-secret `region`, so EnvGene splits the list across
the two files and the deployer keeps only one:

```yaml
REGION_TOKENS:
  - region: eu
    token: ${creds.get("eu-token").secret}
  - region: us
    token: ${creds.get("us-token").secret}
```

OK - a map keyed by `region`. The region is a key, not a value, so each entry holds only its secret, the
list no longer mixes the two, and the whole value stays in the credentials file:

```yaml
REGION_TOKENS:
  eu:
    token: ${creds.get("eu-token").secret}
  us:
    token: ${creds.get("us-token").secret}
```

## How EnvGene Processes Complex Parameters

### During Environment Instance Generation

EnvGene preserves structure and types (map, list, boolean, number, string) and produces a structured effective set. No flattening or string conversion occurs at this stage.

Example effective set output:

```yaml
deploymentConfig:
  replicas: 3
  strategy:
    type: RollingUpdate
    maxUnavailable: 1
  resources:
    limits:
      cpu: 1
      memory: 2Gi
```

### During CMDB Import

CMDB requires complex parameters to be stored as escaped string representations.

EnvGene automatically transforms the YAML object.

Source YAML object:

```yaml
deploymentConfig:
  replicas: 3
  strategy:
    type: RollingUpdate
```

CMDB stores the parameter key separately; the value is the escaped JSON string. Example value:

```json
"{\"replicas\":3,\"strategy\":{\"type\":\"RollingUpdate\"}}"
```

Key points:

- Conversion is automatic
- No manual escaping required
- Original structure drives transformation
- Type fidelity is preserved before serialization

## End-to-End Example

### YAML Definition in Template or Environment-specific parameters

```yaml
parameters:
  serviceConfig:
    service:
      name: payment-api
      port: 8080
    monitoring:
      enabled: true
      endpoints:
        - /health
        - /metrics
```

### Effective Set Output

```yaml
serviceConfig:
  service:
    name: payment-api
    port: 8080
  monitoring:
    enabled: true
    endpoints:
      - /health
      - /metrics
```

### CMDB Imported Representation

```json
"{\"service\":{\"name\":\"payment-api\",\"port\":8080},\"monitoring\":{\"enabled\":true,\"endpoints\":[\"/health\",\"/metrics\"]}}"
```

Result:

- Structure preserved
- Types preserved
- Converted into CMDB-compatible format automatically

## Design Principles for YAML

### Treat YAML as Structured Data

If the parameter represents structured configuration, it must be a YAML object, not a multiline string or a JSON string.

### Preserve Type Integrity

Avoid:

```yaml
replicas: "3"
enabled: "true"
```

Prefer:

```yaml
replicas: 3
enabled: true
```

### Avoid Embedded JSON Inside YAML

Do not embed JSON in YAML values (e.g. `config: '{"limits":{"cpu":"1"}}'`). See [No Manual Escaping](#no-manual-escaping).

## Migration Strategy for Existing Multiline or JSON Strings

If complex parameters already exist as multiline strings or JSON in a string:

1. Identify parameters to migrate:
   - **Multiline:** look for keys whose value uses `|` or `>` (block scalars) with YAML-like or list-like content underneath.
   - **JSON in string:** look for values that are single-quoted or double-quoted JSON (e.g. `'{"key":...}'` or `"{ \"key\": ... }"`).
2. Convert content into structured YAML (native map or list).
3. Validate:
   - Instance generation
   - Effective set output
   - CMDB import result
4. Remove manual escaping where it was used for JSON.
5. Add YAML linting to CI pipelines.

## Operational Impact

Adopting YAML objects improves:

- Maintainability
- Git readability
- Configuration correctness
- CI/CD validation capability
- Reduction of CMDB import failures
- Long-term configuration scalability

## Final Recommendation

- Use native YAML objects only for maps and lists (see [Core Rule](#core-rule)).
- Rely on automatic CMDB transformation and enforce YAML linting in CI/CD.
- Keep configuration declarative and type-safe.

YAML objects enable that; multiline and JSON strings undermine it.
