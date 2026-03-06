# Defining and Managing Complex Parameters in EnvGene Using YAML Objects

- [Defining and Managing Complex Parameters in EnvGene Using YAML Objects](#defining-and-managing-complex-parameters-in-envgene-using-yaml-objects)
  - [1. Purpose of This Guide](#1-purpose-of-this-guide)
  - [2. When to Use This Guide](#2-when-to-use-this-guide)
  - [3. Core Rule](#3-core-rule)
  - [4. Why YAML Objects Are Required](#4-why-yaml-objects-are-required)
    - [4.1 Structural Integrity](#41-structural-integrity)
    - [4.2 Clean and Meaningful Git Diffs](#42-clean-and-meaningful-git-diffs)
    - [4.3 No Manual Escaping](#43-no-manual-escaping)
    - [4.4 Predictable CMDB Transformation](#44-predictable-cmdb-transformation)
  - [5. How to Define Complex Parameters Correctly](#5-how-to-define-complex-parameters-correctly)
    - [5.1 Defining a Map (Object)](#51-defining-a-map-object)
    - [5.2 Defining a List](#52-defining-a-list)
    - [5.3 Defining Nested Structures](#53-defining-nested-structures)
  - [6. How EnvGene Processes Complex Parameters](#6-how-envgene-processes-complex-parameters)
    - [6.1 During Environment Instance Generation](#61-during-environment-instance-generation)
    - [6.2 During CMDB Import](#62-during-cmdb-import)
  - [7. End-to-End Example](#7-end-to-end-example)
    - [7.1 YAML Definition](#71-yaml-definition)
    - [7.2 Effective Set Output](#72-effective-set-output)
    - [7.3 CMDB Imported Representation](#73-cmdb-imported-representation)
  - [8. Design Principles for YAML](#8-design-principles-for-yaml)
    - [8.1 Treat YAML as Structured Data](#81-treat-yaml-as-structured-data)
    - [8.2 Preserve Type Integrity](#82-preserve-type-integrity)
    - [8.3 Avoid Embedded JSON Inside YAML](#83-avoid-embedded-json-inside-yaml)
    - [8.4 Keep Structure Logical](#84-keep-structure-logical)
  - [9. Common Antipatterns](#9-common-antipatterns)
  - [10. Migration Strategy for Existing Multiline Strings](#10-migration-strategy-for-existing-multiline-strings)
  - [11. Operational Impact](#11-operational-impact)
  - [12. Final Recommendation](#12-final-recommendation)

## 1. Purpose of This Guide

This guide explains how to correctly define complex parameters (maps, lists, and nested structures) in EnvGene using native YAML objects instead of multiline strings.

It provides:

- Clear best practices
- Correct vs incorrect examples
- Explanation of EnvGene behavior during:

  - Environment instance generation
  - Effective set generation
  - CMDB import transformation
- End-to-end example of structure preservation and CMDB conversion

This is a practical how-to guide intended for engineers defining configuration in Git-managed EnvGene repositories.

---

## 2. When to Use This Guide

Use this guide when:

- Defining new parameters in EnvGene
- Refactoring existing multiline string parameters
- Debugging CMDB import formatting issues
- Reviewing pull requests involving complex configuration
- Establishing configuration standards across teams

---

## 3. Core Rule

> Always define complex parameters as structured YAML objects. Never use multiline strings for structured configuration.

Complex parameters include:

- Maps (objects)
- Lists (arrays)
- Nested structures combining maps and lists

---

## 4. Why YAML Objects Are Required

### 4.1 Structural Integrity

When defined as YAML objects:

- Types are preserved (map, list, boolean, number, string)
- Nested attributes retain structure
- YAML schema validation works
- Linters and IDE tooling function correctly

When defined as multiline strings:

- Everything becomes a string
- Structure is lost
- No validation is applied
- Type safety is broken

---

### 4.2 Clean and Meaningful Git Diffs

Structured YAML enables semantic diffs:

```diff
resources:
  limits:
-    memory: 512Mi
+    memory: 1Gi
```

Multiline strings create noisy diffs:

```diff
- config: |
-   limits:
-     memory: 512Mi
+ config: |
+   limits:
+     memory: 1Gi
```

Structured YAML improves:

- Code reviews
- Drift detection
- Merge conflict resolution

---

### 4.3 No Manual Escaping

Multiline or escaped JSON string:

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

---

### 4.4 Predictable CMDB Transformation

EnvGene behavior:

1. Preserves structure during:

   - Environment instance generation
   - Effective set generation
2. Converts complex parameters into escaped string representations only during CMDB import

When YAML is structured correctly:

- Transformation is deterministic
- JSON structure is valid
- No manual formatting is required
- Debugging is straightforward

---

## 5. How to Define Complex Parameters Correctly

### 5.1 Defining a Map (Object)

Correct:

```yaml
parameters:
  resourceLimits:
    cpu: 500m
    memory: 1Gi
```

Incorrect:

```yaml
parameters:
  resourceLimits: |
    cpu: 500m
    memory: 1Gi
```

---

### 5.2 Defining a List

Correct:

```yaml
parameters:
  allowedIPs:
    - 10.10.0.1
    - 10.10.0.2
    - 10.10.0.3
```

Incorrect:

```yaml
parameters:
  allowedIPs: |
    - 10.10.0.1
    - 10.10.0.2
```

---

### 5.3 Defining Nested Structures

Recommended pattern:

```yaml
parameters:
  deploymentConfig:
    replicas: 3
    strategy:
      type: RollingUpdate
      maxUnavailable: 1
    resources:
      limits:
        cpu: 1
        memory: 2Gi
      requests:
        cpu: 500m
        memory: 1Gi
```

Antipattern (embedded JSON):

```yaml
parameters:
  deploymentConfig: '{"replicas":3,"strategy":{"type":"RollingUpdate"}}'
```

---

## 6. How EnvGene Processes Complex Parameters

### 6.1 During Environment Instance Generation

EnvGene:

- Preserves nested structure
- Maintains original types:

  - Map
  - List
  - Boolean
  - Number
  - String
- Produces a structured effective set

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

No flattening or string conversion occurs at this stage.

---

### 6.2 During CMDB Import

CMDB requires complex parameters to be stored as escaped string representations.

EnvGene automatically transforms the YAML object.

Source YAML object:

```yaml
deploymentConfig:
  replicas: 3
  strategy:
    type: RollingUpdate
```

CMDB representation:

```json
"{\"replicas\":3,\"strategy\":{\"type\":\"RollingUpdate\"}}"
```

Key points:

- Conversion is automatic
- No manual escaping required
- Original structure drives transformation
- Type fidelity is preserved before serialization

---

## 7. End-to-End Example

### 7.1 YAML Definition

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

---

### 7.2 Effective Set Output

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

---

### 7.3 CMDB Imported Representation

```json
"{\"service\":{\"name\":\"payment-api\",\"port\":8080},\"monitoring\":{\"enabled\":true,\"endpoints\":[\"/health\",\"/metrics\"]}}"
```

Result:

- Structure preserved
- Types preserved
- Converted into CMDB-compatible format automatically

---

## 8. Design Principles for YAML

### 8.1 Treat YAML as Structured Data

If the parameter represents structured configuration, it must be a YAML object, not text.

---

### 8.2 Preserve Type Integrity

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

---

### 8.3 Avoid Embedded JSON Inside YAML

Do not use:

```yaml
config: '{"limits":{"cpu":"1"}}'
```

If you see JSON inside YAML, it is almost always incorrect.

---

### 8.4 Keep Structure Logical

Avoid excessive nesting unless required by design.
Prefer readable, domain-aligned structure.

---

## 9. Common Antipatterns

| Antipattern                 | Risk Introduced                      |
| ---------------------------- | ------------------------------------ |
| Multiline YAML as string     | No validation, diff noise, type loss |
| Escaped JSON string          | Manual escaping, readability issues  |
| Stringified booleans/numbers | Type corruption                      |
| Mixed data types in lists    | Runtime inconsistency                |
| Deep arbitrary nesting       | Difficult overrides and maintenance  |

---

## 10. Migration Strategy for Existing Multiline Strings

If complex parameters already exist as multiline strings:

1. Identify parameters using `|`.
2. Convert content into structured YAML.
3. Validate:

   - Instance generation
   - Effective set output
   - CMDB import result
4. Remove manual escaping.
5. Add YAML linting to CI pipelines.

---

## 11. Operational Impact

Adopting YAML objects improves:

- Maintainability
- Git readability
- Configuration correctness
- CI/CD validation capability
- Reduction of CMDB import failures
- Long-term configuration scalability

---

## 12. Final Recommendation

For all complex parameters:

- Define maps and lists as native YAML objects.
- Allow automatic transformation during CMDB import.
- Preserve structural and type integrity.
- Enforce YAML linting in CI/CD.
- Never use multiline strings for structured configuration.

Configuration should be declarative, structured, and type-safe. YAML objects enable that. Multiline strings undermine it.
