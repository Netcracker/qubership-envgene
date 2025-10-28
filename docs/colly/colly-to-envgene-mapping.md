# Mapping of Colly attributes to EnvGene attributes

- [Mapping of Colly attributes to EnvGene attributes](#mapping-of-colly-attributes-to-envgene-attributes)
  - [Mapping table](#mapping-table)
    - [`env_definition.yml` example](#env_definitionyml-example)
  - [To Discuss](#to-discuss)
  - [To Implement](#to-implement)

## Mapping table

| Colly Object | Colly Attribute     | Mandatory in Colly  | Default in Colly | Attribute Type in Colly                                       | EnvGene Repository  | Location in EnvGene                        | Attribute Type in EnvGene | Description                                       |
|--------------|---------------------|---------------------|------------------|---------------------------------------------------------------|---------------------|--------------------------------------------|---------------------------|---------------------------------------------------|
| Environment  | `owners`            | No                  | ""               | array of string                                               | instance            | `env_definition.metadata.owners`           | array of string           | Users responsible for the Environment             |
| Environment  | `teams`             | No                  | ""               | array of string                                               | instance            | `env_definition.metadata.teams`            | array of string           | Teams assigned to the Environment                 |
| Environment  | `status`            | No                  | `FREE`           | enum [`IN_USE`, `RESERVED`, `FREE`, `MIGRATING`]              | instance            | `env_definition.metadata.status`           | string                    | Current status of the Environment                 |
| Environment  | `expirationDate`    | No                  | ""               | string (LocalDate "yyyy-MM-dd")                               | instance            | `env_definition.metadata.expirationDate`   | string                    | Date until which Environment is allocated         |
| Environment  | `type`              | No                  | `ENVIRONMENT`    | enum [`ENVIRONMENT`, `CSE_TOOLSET`, `DESIGN_TIME`,            | instance            | `env_definition.metadata.type`             | string                    | Defines the technical category of the Environment |
|              |                     |                     |                  | `APP_DEPLOYER`, `INFRASTRUCTURE`, `UNDEFINED`]                |                     |                                            |                           |                                                   |
| Environment  | `role`              | No                  | ""               | enum [`Dev`, `QA`, `Project CI`, `SaaS`, `Joint CI`, `Other`] | instance            | `env_definition.metadata.role`             | string                    | Defines usage role of the Environment             |
| Environment  | `labels`            | No                  | []               | array of string                                               | instance            | `env_definition.metadata.labels`           | array of string           | Custom labels for the Environment                 |
| Environment  | `description`       | No                  | ""               | string                                                        | instance            | `env_definition.metadata.description`      | string                    | Free-form Environment description                 |
| Environment  | `deploymentStatus`  | No                  | ""               | enum [`DEPLOYED`, `FAILED`, `IN_PROGRESS`, `NOT_STARTED`]     | None                | None                                       | string                    | Environment deployment status                     |
| Environment  | `ticketLinks`       | No                  | []               | array of string                                               | None                | None                                       | array of string           | Custom list of ticket IDs                         |
| Cluster      | `description`       | No                  | ""               | string                                                        | instance            | **TBD**                                    | string                    | Free-form Cluster description                     |

### `env_definition.yml` example

```yaml
metadata:
  owners:
    - "user1"
    - "user2"
  teams:
    - "team-a"
    - "team-b"
  status: "IN_USE"
  expirationDate: "2024-12-31"
  type: "ENVIRONMENT"
  role: "Dev"
  labels:
    - "prod"
    - "priority-high"
  description: "very important env"
```

## To Discuss

- [ ] Where to store the `description` of a Cluster
- [ ] is `ticketLinks` required?
- [ ] Chekov linter errors - https://github.com/Netcracker/qubership-envgene/actions/runs/18886399036/job/53902750553

## To Implement

1. Change the formation of the macros `current_env.description` and `current_env.owners` taking into account the metadata section and migration
2. Add the `deployPostfix` attribute to the Namespace
3. Remove the `deploymentVersion` attribute from the Environment
