# Mapping of Colly attributes to EnvGene attributes

- [Mapping of Colly attributes to EnvGene attributes](#mapping-of-colly-attributes-to-envgene-attributes)
  - [Mapping table](#mapping-table)
  - [To Discuss](#to-discuss)
  - [To Implement](#to-implement)

## Mapping table

| Colly Object | Colly Attribute     | Mandatory in Colly  | Default in Colly | Attribute Type                                                | EnvGene Repo  | Location in EnvGene                        | Description                                       |
|--------------|---------------------|---------------------|------------------|---------------------------------------------------------------|---------------|--------------------------------------------|---------------------------------------------------|
| Environment  | `owners`            | No                  | ""               | string                                                        | instance      | `env_definition.metadata.owners`           | User responsible for the Environment              |
| Environment  | `teams`             | No                  | ""               | string                                                        | instance      | `env_definition.metadata.teams`             | Team assigned to the Environment                  |
| Environment  | `EnvironmentStatus` | No                  | `FREE`           | enum [`IN_USE`, `RESERVED`, `FREE`, `MIGRATING`]              | instance      | `env_definition.metadata.status`           | Current status(???) of the Environment            |
| Environment  | `expirationDate`    | No                  | ""               | LocalDate ("yyyy-MM-dd")                                      | instance      | `env_definition.metadata.expirationDate`   | Date until which Environment is allocated         |
| Environment  | `EnvironmentType`   | No                  | `ENVIRONMENT`    | enum [`ENVIRONMENT`, `CSE_TOOLSET`, `DESIGN_TIME`,            | instance      | `env_definition.metadata.type`             | Defines the technical category of the Environment |
|              |                     |                     |                  | `APP_DEPLOYER`, `INFRASTRUCTURE`, `UNDEFINED`]                |               |                                            |                                                   |
| Environment  | `EnvironmentRole`   | No                  | ""               | enum [`Dev`, `QA`, `Project CI`, `SaaS`, `Joint CI`, `Other`] | instance      | `env_definition.metadata.role`             | Defines usage role of the Environment             |
| Environment  | `labels`            | No                  | []               | list of string                                                | instance      | `env_definition.metadata.labels`           | Custom labels for the Environment                 |
| Environment  | `description`       | No                  | ""               | string                                                        | instance      | `env_definition.metadata.description`      | Free-form Environment description                 |
| Environment  | `deploymentStatus`  | No                  | ""               | enum [`DEPLOYED`, `FAILED`, `IN_PROGRESS`, `NOT_STARTED`]     | None          | None                                       | Environment deployment status                     |
| Environment  | `ticketLinks`       | No                  | []               | list (type unspecified)                                       | None          | None                                       | Custom list of ticket ids                         |
| Cluster      | `description`       | No                  | ""               | string                                                        | instance      | **TBD**                                    | Free-form Cluster description                     |

## To Discuss

- [ ] Where to store the `description` of a Cluster

## To Implement

1. Change the formation of the macros `current_env.description` and `current_env.owners` taking into account the metadata section and migration
