# Override Application and Registry Definitions

- [Override Application and Registry Definitions](#override-application-and-registry-definitions)
  - [Overview](#overview)
  - [Override Directory Structure](#override-directory-structure)
  - [Override Matching Rules](#override-matching-rules)
    - [Filename Matching](#filename-matching)
    - [Matching Example](#matching-example)
  - [Override Processing Flow](#override-processing-flow)
    - [Processing Stages](#processing-stages)
    - [Post-Render Processing](#post-render-processing)
  - [Override Semantics](#override-semantics)
    - [Full-File Replacement](#full-file-replacement)
    - [Override Example](#override-example)
    - [Final Effective Definition](#final-effective-definition)
  - [Overriding Registry Definitions](#overriding-registry-definitions)
  - [Override Definitions Without Matching Templates](#override-definitions-without-matching-templates)
  - [Interaction with `appdefs.overrides`](#interaction-with-appdefsoverrides)
    - [Processing Order](#processing-order)
    - [Precedence Rules](#precedence-rules)
  - [CMDB Export Behavior](#cmdb-export-behavior)
  - [Additional Notes](#additional-notes)

## Overview

EnvGene supports overriding generated Application Definitions (AppDefs)
and Registry Definitions (RegDefs) using user-provided definition files.

Override definitions allow instance repositories to customize generated
definitions without modifying template sources.

The final effective definitions produced after override processing are
used during downstream deployment and CMDB integration workflows.

## Override Directory Structure

Generated definitions are created in the centralized locations:

- `/genDefs/appDefs/*`
- `/genDefs/regDefs/*`

User-provided override definitions must be placed in:

- `/userDefs/appDefs/*`
- `/userDefs/regDefs/*`

## Override Matching Rules

Override definitions are matched to generated definitions by filename.

### Filename Matching

The filename determines which generated definition is overridden.

The YAML `name` field is not used for override matching.

If the filename and YAML `name` field differ, filename matching still
determines the override target.

### Matching Example

Generated definition:

```text
/genDefs/appDefs/application-1.yml
```

Override definition:

```text
/userDefs/appDefs/application-1.yml
```

In this case, the override definition replaces the generated definition.

## Override Processing Flow

Override processing occurs after Jinja template rendering is completed.

### Processing Stages

Processing flow:

1. Render AppDef and RegDef templates
2. Generate centralized definitions
3. Apply user override definitions
4. Produce final effective definitions
5. Export effective definitions to downstream jobs and CMDB

### Post-Render Processing

Override processing is applied after template rendering is completed.

This allows override definitions to operate on fully rendered
environment-specific values and avoids requiring Jinja-aware override
files.

## Override Semantics

Override definitions use full-file replacement semantics.

If a matching override definition exists, the generated definition is
fully replaced by the override definition.

Fields not present in the override definition are removed from the final
effective definition.

### Full-File Replacement

Generated AppDef:

```yaml
name: application-1
artifactId: application-1
groupId: org.qubership
supportParallelDeploy: true
```

Override AppDef:

```yaml
name: application-1
artifactId: custom-application
```

### Override Example

Override file location:

```text
/userDefs/appDefs/application-1.yml
```

### Final Effective Definition

```yaml
name: application-1
artifactId: custom-application
```

Result:

- `groupId` is removed
- `supportParallelDeploy` is removed
- only fields defined in the override file remain

## Overriding Registry Definitions

Registry Definitions (RegDefs) use the same override mechanism.

Example:

Generated RegDef:

```text
/genDefs/regDefs/registry-1.yml
```

Override RegDef:

```text
/userDefs/regDefs/registry-1.yml
```

If both files exist, the override RegDef becomes the final effective
definition.

## Override Definitions Without Matching Templates

Override definitions only apply to existing generated definitions.

Example:

```text
/userDefs/appDefs/nonexistent.yml
```

If no generated definition exists for `nonexistent.yml`, the override
definition is ignored.

## Interaction with `appdefs.overrides`

The existing `appdefs.overrides` Jinja-based mechanism and file-based
override processing are independent features.

### Processing Order

1. `appdefs.overrides` applies during template rendering
2. File-based override processing applies after rendering is completed

### Precedence Rules

If both mechanisms modify the same definition, file-based overrides take
precedence because they are applied later in the processing flow.

## CMDB Export Behavior

The `cmdb_import` pipeline job exports the final effective definitions
after override processing is completed.

CMDB therefore receives the same definitions used during downstream
deployment processing.

## Additional Notes

- Override processing is performed on a per-file basis
- Override definitions do not modify template source files
- Override definitions are instance-specific customizations
- Removing an override definition restores the generated definition as
  the effective definition during the next pipeline execution
