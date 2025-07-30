
# Solution Descriptor Processing

- [Solution Descriptor Processing](#solution-descriptor-processing)
  - [Problem Statement](#problem-statement)
  - [Proposed Approach](#proposed-approach)
    - [Requirements](#requirements)
    - [Instance Repository Pipeline Parameters](#instance-repository-pipeline-parameters)
      - [`SD_DATA` Example](#sd_data-example)
    - [SD merge](#sd-merge)
      - [Merge Terms](#merge-terms)
      - [Merge Rules](#merge-rules)
      - [Merge Assumptions](#merge-assumptions)

## Problem Statement

EnvGene requires the Solution Descriptor, as it lacks knowledge of whole Solution's application scope to calculate the Effective Set

## Proposed Approach

It is proposed to enhance EnvGene with the capability to retrieve SDs in artifact or JSON format and store them in a repository. These SDs will be utilized for Effective Set calculations and will also be accessible to external systems for deployment purposes.

To support the deployment of individual applications, the use of Delta SDs is suggested.

### Requirements

1. SD processing must occur **before** to the `generate_effective_set_job`
2. SD processing should take place in a separate job
3. The Full and Delta SDs files should be stored in repository and job artifacts
4. SD merge must occur according to [SD Merge](#sd-merge)

### Instance Repository Pipeline Parameters

| Attribute | Type | Mandatory | Description | Default | Example |
|---|---|---|---|---|---|
| `SD_VERSION` | string | no | System downloads the artifact. System overrides the file /environments/<ENV_NAME>/Inventory/solution-descriptor/sd.yml with the content provided in the artifact. If the file is absent, it will be generated | None |`MONITORING:0.64.1` |
| `SD_DATA` | string | no | System overrides the file /environments/<ENV_NAME>/Inventory/solution-descriptor/sd.yml with the content provided in SD_DATA. If the file is absent, it will be generated | None | [Example](#sd_data-example) |
| `SD_DELTA` | boolean | no | If `true` system overrides the file `/environments/<ENV_NAME>/Inventory/solution-descriptor/delta_sd.yml` with the content provided in `SD_DATA`. `SD_VERSION` is not supported. If the file is absent, it will be generated. System merges the content provided in `SD_DATA` into the file `/environments/<ENV_NAME>/Inventory/solution-descriptor/sd.yml`. If `false` system overrides the file `/environments/<ENV_NAME>/Inventory/solution-descriptor/sd.yml` with the content provided in `SD_DATA`. If the file is absent, it will be generated | `false` | `true` |
| `SD_SOURCE_TYPE` | enumerate[`artifact`,`json`] | TBD | Defines the method by which SD is passed in the `SD_DATA` or `SD_VERSION` attributes. If `artifact`, an SD artifact is expected in `SD_VERSION` in app:ver notation. If `json`, SD content is expected in `SD_DATA` in JSON-in-string format. The system should transform it into YAML format, and save it to the repository | TBD | `artifact` |

#### `SD_DATA` Example

```text
'{"version":"2.1","type":"solutionDeploy","deployMode":"composite","applications":[{"version":"MONITORING:0.64.1","deployPostfix":"platform-monitoring"},{"version":"postgres:1.32.6","deployPostfix":"postgresql"},{"version":"postgres-services:1.32.6","deployPostfix":"postgresql"},{"version":"postgres:1.32.6","deployPostfix":"postgresql-dbaas"}]}'
```

The same in YAML:

```yaml
version: 2.1
type: "solutionDeploy"
deployMode: "composite"
applications:
  - version: "MONITORING:0.64.1"
    deployPostfix: "platform-monitoring"
  - version: "postgres:1.32.6"
    deployPostfix: "postgresql"
  - version: "postgres-services:1.32.6"
    deployPostfix: "postgresql"
  - version: "postgres:1.32.6"
    deployPostfix: "postgresql-dbaas"
```

### SD merge

#### Merge Terms

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

#### Merge Rules

1. For each Matching Application in Full SD, replace the Application Version with the one from Delta SD. See use cases UC-1-X as examples
2. For each New Application (See use cases UC-2-X as examples):
   1. Append the New Application from the Delta SD to the end of the applications list in the Full SD.
   2. Append the Alias of the New Application to the end of the apps list in the chunk with the equal as in the Delta SD
3. Each Duplicating Application must remain unchanged
4. The order of elements in the applications list must remain unchanged
5. The order of elements in the deployGraph list must remain unchanged
6. The order of elements in the apps list must remain unchanged

#### Merge Assumptions

1. The values of the attributes version, type, and `deployMode` in both Full and Delta SDs must match.
2. All Applications must conform to the same model as in both Full and Delta SDs. Valid models include:
   1. `<application:version>`
   2. `version: <application:version>`
      `deployPostfix:  <>`
   3. `version: <application:version>`
      `deployPostfix: <>`
      `alias: <>`
3. If the Full SD does not contain a `deployGraph`, the Delta SD must not contain one either.
4. If either the Full or Delta SD contains a `deployGraph`, then all applications listed in applications must also be present in the `deployGraph`.
5. The `deployGraph` in the Delta SD can contains applications that are not listed in its own applications section. (This is a case where the Delta SD contains a complete `deployGraph`)
6. The Delta SD must not contain any chunks that are not present in the Full SD.
7. If the Delta SD introduces a New Application, it must also contains a `deployGraph` that contains this New Application
