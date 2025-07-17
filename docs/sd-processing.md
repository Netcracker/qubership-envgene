
# Solution Descriptor Processing

- [Solution Descriptor Processing](#solution-descriptor-processing)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
    - [Requirements](#requirements)
    - [SD Types](#sd-types)
      - [Full SD](#full-sd)
      - [Delta SD](#delta-sd)
    - [Instance Repository Pipeline Parameters](#instance-repository-pipeline-parameters)
      - [`SD_DATA` Example](#sd_data-example)
    - [SD merge](#sd-merge)
      - [`basic-merge` SD Merge Mode](#basic-merge-sd-merge-mode)
        - [`basic-merge` SD Merge Mode Terms](#basic-merge-sd-merge-mode-terms)
        - [`basic-merge` SD Merge Mode Assumptions](#basic-merge-sd-merge-mode-assumptions)
        - [`basic-merge` SD Merge Mode Rules](#basic-merge-sd-merge-mode-rules)
      - [`basic-exclusion-merge` SD Merge Mode](#basic-exclusion-merge-sd-merge-mode)
        - [`basic-exclusion-merge` SD Merge Mode Terms](#basic-exclusion-merge-sd-merge-mode-terms)
        - [`basic-exclusion-merge` SD Merge Mode Assumptions](#basic-exclusion-merge-sd-merge-mode-assumptions)
        - [`basic-exclusion-merge` SD Merge Mode Rules](#basic-exclusion-merge-sd-merge-mode-rules)
      - [`extended-merge` SD Merge Mode](#extended-merge-sd-merge-mode)
        - [`extended-merge` SD Merge Mode Terms](#extended-merge-sd-merge-mode-terms)
        - [`extended-merge` Merge Mode Assumptions](#extended-merge-merge-mode-assumptions)
        - [`extended-merge` SD Merge Mode Rules](#extended-merge-sd-merge-mode-rules)
  - [Test Cases](#test-cases)

## Problem Statement

EnvGene requires the Solution Descriptor (SD), as it lacks knowledge of whole Solution's application scope as well as application's microservices scope to calculate the Effective Set

## Proposed Approach

It is proposed to enhance EnvGene with the capability to retrieve SDs in artifact or JSON format and store them in a repository. These SDs will be utilized for Effective Set calculations and will also be accessible to external systems for deployment purposes.

To support the deployment of individual applications, the use of Delta SDs is suggested.

### Requirements

1. SD processing must occur **before** to the `generate_effective_set_job`
2. SD processing should take place in a separate job
3. The Full and Delta SDs files should be stored in repository and job artifacts
4. SD merge must occur according to [SD Merge](#sd-merge)

### SD Types

In EnvGene, there are two types of SDs that differ in their purpose and composition:

#### Full SD

Defines the complete application composition of a solution. There can be only one Full SD per environment, located at the path `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/sd.yml`.

#### Delta SD

A partial Solution Descriptor that contains incremental changes to be applied to the Full SD. Delta SDs enable selective updates to solution components without requiring a complete SD replacement. There can be only one Delta SD per environment, located at the path `/environments/<cloud-name>/<env-name>/Inventory/solution-descriptor/delta_sd.yml`.

### Instance Repository Pipeline Parameters

| Attribute | Type | Mandatory | Description | Default | Example |
|---|---|---|---|---|---|
| `SD_VERSION` | string | no | Specifies one or more SD artifacts in `application:version` notation passed via a `\n` separator. EnvGene downloads and sequentially merges them in the mode described in `SD_MULTIPLE_MERGE_MODE`, where subsequent `application:version` takes priority over the previous one. Saves the result to [Delta SD](#delta-sd), then merges with [Full SD](#full-sd) using `SD_REPO_MERGE_MODE` merge mode | None | `solution:0.64.1` |
| `SD_DATA` | string | no | Specifies the **list** of contents of one or more SD in JSON-in-string format. EnvGene sequentially merges them in the mode described in `SD_MULTIPLE_MERGE_MODE`, where subsequent element takes priority over the previous one. Saves the result to [Delta SD](#delta-sd), then merges with [Full SD](#full-sd) using `SD_REPO_MERGE_MODE` merge mode | None | [Example](#sd_data-example) |
| `SD_SOURCE_TYPE` | enumerate[`artifact`,`json`] | TBD | Determines the method by which SD is passed in the `SD_VERSION`/`SD_DATA` attributes. If `artifact`, an SD artifact is expected in `SD_VERSION` in app:ver notation. If `json`, SD content is expected in `SD_DATA` in JSON-in-string format | TBD | `artifact` |
| `SD_DELTA` | enumerate[`true`, `false`] | no | Deprecated. When `true`: behaves identically to `SD_REPO_MERGE_MODE: extended-merge`. When `false` behaves identically to `SD_REPO_MERGE_MODE: replace`. If both `SD_DELTA` and `SD_REPO_MERGE_MODE` are provided, `SD_REPO_MERGE_MODE` takes precedence | `true` | `false` |
| `SD_MULTIPLE_MERGE_MODE` | enumerate[`basic-merge`, `extended-merge`] | no | Defines SD merge mode between SDs passed in `SD_VERSION`/`SD_DATA`. See details in [SD Merge](#sd-merge) | `basic-merge` | `extended-merge` |
| `SD_REPO_MERGE_MODE` | enumerate[`basic-merge`, `basic-exclusion-merge`, `extended-merge`, `replace`] | no | Defines SD merge mode between incoming SD and already existed in repository SD. See details in [SD Merge](#sd-merge) | `basic-merge` | `extended-merge` |

#### `SD_DATA` Example

Single SD:

```text
'[{"version":2.1,"type":"solutionDeploy","deployMode":"composite","applications":[{"version":"MONITORING:0.64.1","deployPostfix":"platform-monitoring"},{"version":"postgres:1.32.6","deployPostfix":"postgresql"}]},{"version":2.1,"type":"solutionDeploy","deployMode":"composite","applications":[{"version":"postgres-services:1.32.6","deployPostfix":"postgresql"},{"version":"postgres:1.32.3","deployPostfix":"postgresql-dbaas"}]}]'
```

Multiple SD:

```text
'[{[{"version": 2.1, "type": "solutionDeploy", "deployMode": "composite", "applications": [{"version": "MONITORING:0.64.1", "deployPostfix": "platform-monitoring"}, {"version": "postgres:1.32.6", "deployPostfix": "postgresql"}]}, {"version": 2.1, "type": "solutionDeploy", "deployMode": "composite", "applications": [{"version": "postgres-services:1.32.6", "deployPostfix": "postgresql"}, {"version": "postgres:1.32.6", "deployPostfix": "postgresql-dbaas"}]}]}]'
```

> [!NOTE]
> `SD_DATA` is a list even in single SD case

### SD merge

SD merging occurs in the following cases:

1. **Multiple SD Input**: When the Multiple SD are provided in `SD_VERSION` or `SD_DATA` parameters. The system merges them sequentially, giving priority to later SDs over earlier ones.

2. **Repository Merge**: When `SD_VERSION` or `SD_DATA` parameters are provided and a [Full SD](#full-sd) already exists in the repository for the target environment. The system merges the incoming SD with the existing repository SD.

> [!NOTE]
> When processing Multiple SD in `SD_VERSION`/`SD_DATA` variables, the first SD is treated as Full,
> and subsequent ones as Delta.

There are four merge modes. They differ in their algorithms and output results:

1. [`basic-merge`](#basic-merge-sd-merge-mode): The merge produces a SD sufficient for EnvGene to calculate the Effective Set. In this mode, SD applications and components are added and/or modified.
2. [`basic-exclusion-merge`](#basic-exclusion-merge-sd-merge-mode): The merge produces a SD sufficient for EnvGene to calculate the Effective Set. In this mode, SD applications and components are removed and/or modified.
3. [`extended-merge`](#extended-merge-sd-merge-mode): The merge produces an SD that can be used (with certain limitations) outside of EnvGene, for deployment or delivery purposes as well as Effective Set calculation by EnvGene. In this mode, SD applications and components are added and/or modified.
4. `replace`: Performs complete replacement - the incoming SD entirely overwrites the repository SD without merging.

#### `basic-merge` SD Merge Mode

The simple merge strategy designed specifically for Effective Set calculation in EnvGene. This mode:

- Maintains minimal SD structure (only `applications` attribute)
- Preserves the original order of applications
- Typical use case: Incremental updates to solution components when you need to modify versions of existing applications or add new ones

##### `basic-merge` SD Merge Mode Terms

The following set of terms is used to describe the rules and assumptions of SD merge

**Application** - is an entry in a SD's applications list

**Application Name** - attribute of an Application, equals:

- `version.split(':')[0]`

**Application Version** - attribute of an Application, equals:

- `version.split(':')[0]`

**Matching Application** - is an entry in the Full SD's applications list that has a corresponding entry in the Delta SD's applications list. These corresponding entries must match in the following fields:

- Application Name
- `deployPostfix`

**Duplicating Application** - is an entry in the Full SD's applications list that has a corresponding entry in the Delta SD's applications list. These corresponding entries must match in the following fields:

- Application Name
- Application Version
- `deployPostfix`

**New Application** - is an entry in the Delta SD's applications list that has NOT a corresponding entry in the Full SD's applications list. The matching rule the same as for Matching application

##### `basic-merge` SD Merge Mode Assumptions

1. Valid Application models:
   1. `version: <application:version>`
      `deployPostfix:  <>`
   2. `version: <application:version>`
      `deployPostfix: <>`
      `alias: <>`

##### `basic-merge` SD Merge Mode Rules

1. For each Matching Application in Full SD, replace the Application Version with the one from Delta SD
2. For each New Application, append the New Application from the Delta SD to the end of the applications list in the Full SD
3. Each Duplicating Application must remain unchanged
4. Resulting SD must not contain any attributes other than `application`
5. Application in the Resulting SD may contain `alias`

#### `basic-exclusion-merge` SD Merge Mode

A variation of basic merge that supports application removal. This mode:

- Additionally allows removal of duplicate applications
- Rejects new applications not present in original SD (throws warning)
- Maintains the same minimal SD structure as `basic-merge`
- Typical use case: Creating reduced solution configurations by removing unnecessary components

##### `basic-exclusion-merge` SD Merge Mode Terms

The same as for [`basic-merge`](#basic-merge-sd-merge-mode-terms)

##### `basic-exclusion-merge` SD Merge Mode Assumptions

The same as for [`basic-merge`](#basic-merge-sd-merge-mode-assumptions)

##### `basic-exclusion-merge` SD Merge Mode Rules

1. For each Matching Application in Full SD, replace the Application Version with the one from Delta SD
2. For each New Application, throw readable warning log message
3. For each Duplicating Application, remove Application
4. Resulting SD must not contain any attributes other than `application`
5. Application in the Resulting SD may contain `alias`

#### `extended-merge` SD Merge Mode

The comprehensive merge strategy that maintains full SD structure for deployment purposes. This mode:

- Handles both applications list and deployment graph (`deployGraph`)
- Preserves all SD attributes (version, type, deployMode) with consistency checks
- Maintains strict ordering in all lists (applications, chunks, apps)
- Requires complete deployGraph consistency when present
- Typical use case: Where both EnvGene and deployment systems need the SD

##### `extended-merge` SD Merge Mode Terms

The following set of terms is used to describe the rules and assumptions of SD merge

**Application** - is an entry in a SD's applications list

**Application Name** - attribute of an Application, equals:

- `split(':')[0]` if Application is a string
- `version.split(':')[0]` if Application is a map

**Application Version** - attribute of an Application, equals:

- `split(':')[0]` if Application is a string
- `version.split(':')[0]` if Application is a map

**Matching Application** - is an entry in the Full SD's applications list that has a corresponding entry in the Delta SD's applications list. These corresponding entries must match in the following fields:

- Application Name
- `deployPostfix` (if it present in Application)
- `alias` (if it present in Application)

**Duplicating Application** - is an entry in the Full SD's applications list that has a corresponding entry in the Delta SD's applications list. These corresponding entries must match in the following fields:

- Application Name
- Application Version
- `deployPostfix` (if it present in Application)
- `alias` (if it present in Application)

**New Application** - is an entry in the Delta SD's applications list that has NOT a corresponding entry in the Full SD's applications list. The matching rule the same as for Matching application

**Application Alias** - Uniquely identifies an application within a specific SD. Is the alias attribute of an entry in the applications list. Applications are identified within the `deployGraph` using their Application Alias in the apps section. This attribute is optional, and its default value is determined as follows:

- if `deployPostfix` is not present, the alias defaults to the Application Name
- if `deployPostfix` is present, the alias defaults to the Application Name + : + `deployPostfix` (concatenation of Application Name, a colon, and `deployPostfix`)

**Chunk** - is an entry in a SD's `deployGraph` list. A Сhunk is uniquely identified by its name attribute within a specific SD

##### `extended-merge` Merge Mode Assumptions

1. The values of the attributes version, type, and `deployMode` in both Full and Delta SDs must match.
2. All Applications must conform to the same model as in both Full and Delta SDs. Valid models include:
   1. `<application:version>`
   2. `version: <application:version>`
      `deployPostfix:  <>`
   3. `version: <application:version>`
      `deployPostfix: <>`
      `alias: <>`
3. If the Full SD does not contain a `deployGraph`, the Delta SD must not contain one either.
4. If either the Full or Delta SD contains a `deployGraph`, then all applications listed in applications must also be present in the `deployGraph`
5. The `deployGraph` in the Delta SD can contains applications that are not listed in its own applications section. (This is a case where the Delta SD contains a complete `deployGraph`)
6. The Delta SD must not contain any chunks that are not present in the Full SD
7. If the Delta SD introduces a New Application, it must also contains a `deployGraph` that contains this New Application

##### `extended-merge` SD Merge Mode Rules

1. For each Matching Application in Full SD, replace the Application Version with the one from Delta SD. See use cases UC-1-X as examples
2. For each New Application (See use cases UC-2-X as examples):
   1. Append the New Application from the Delta SD to the end of the applications list in the Full SD
   2. Append the Alias of the New Application to the end of the apps list in the chunk with the equal as in the Delta SD
3. Each Duplicating Application must remain unchanged
4. The order of elements in the applications list must remain unchanged
5. The order of elements in the deployGraph list must remain unchanged
6. The order of elements in the apps list must remain unchanged

## Test Cases

1. [SD processing](/docs/test-cases/sd-processing.md)
