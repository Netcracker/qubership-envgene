# API Enhancement of according to the Customer requirements

- [API Enhancement of according to the Customer requirements](#api-enhancement-of-according-to-the-customer-requirements)
  - [Environment](#environment)
  - [Namespace](#namespace)
  - [Cluster](#cluster)
  - [Colly instance](#colly-instance)
  - [To discuss](#to-discuss)

## Environment

| Colly Attribute  | Attribute Type                                                | Description                                                                                                                                    |
|------------------|---------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`           | string                                                        | Environment name, cannot be changed after creation                                                                                             |
| `status`         | enum [`PLANNED`, `FREE`, `IN_USE`, `RESERVED`, `DEPRECATED`]  | Current status of the Environment                                                                                                              |
| `role`           | enum [`Dev`, `QA`, `Project CI`, `SaaS`, `Joint CI`, `Other`] | Defines usage role of the Environment                                                                                                          |
| `teams`          | string                                                        | Teams assigned to the Environment. If there are several teams, their names are separated by commas.                                            |
| `owners`         | string                                                        | People responsible for the Environment. If there are several, their names are separated by commas.                                             |
| `productSDs`     | list of strings                                               | List of Solution Descriptors with type `product` in `<name>:<version>` notation, which are currently successfully deployed in this environment |
| `projectSDs`     | list of strings                                               | List of Solution Descriptors with type `project` in `<name>:<version>` notation, which are currently successfully deployed in this environment |
| `infraSDs`       | list of strings                                               | List of Solution Descriptors with type `infra` in `<name>:<version>` notation, which are currently successfully deployed in this environment   |
| Last Deploy Date | string, date-time                                             | TBD                                                                                                                                            |
| `description`    | string                                                        | Free-form Environment description                                                                                                              |
| `namespaces`     | list of [Namespace](#namespace) objects                       | List of associated namespaces                                                                                                                  |
| `cluster`        | [Cluster](#cluster) object                                    | Associated cluster                                                                                                                             |
| Last login date  | string, date-time                                             | TBD                                                                                                                                            |

## Namespace

| Colly Attribute                  | Attribute Type | Description                                                                                                                      |
|----------------------------------|----------------|----------------------------------------------------------------------------------------------------------------------------------|
| `name`                           | string         | Namespace name                                                                                                                   |

## Cluster

| Colly Attribute                  | Attribute Type | Description                                                                                                                      |
|----------------------------------|----------------|----------------------------------------------------------------------------------------------------------------------------------|
| `name`                           | string         | Cluster name, cannot be changed after creation                                                                                   |
| `syncStatus.lastSyncResult`      | string         | Determines the sync status for Cluster: if at least one object from the cluster was successfully read, the sync is considered successful |
| `syncStatus.lastSyncCompletedAt` | string         | Time of the last successful sync                                                                                                 |

## Colly instance

| Colly Attribute | Attribute Type   | Description                                                   |
|-----------------|----------------- |---------------------------------------------------------------|
| `syncInterval`  | string, duration | Period of synchronization with the cluster in ISO 8601 format |

## To discuss

- [ ] `status`

  - What is `to be deprecated`? Why do we not have `deprecated`, `deleted`, or `not used` states?
  - Do we need `MIGRATING` (meaning the upgrade is in progress)?
  - Propose ![env-state-machine.drawio.png](/docs/images/env-state-machine.drawio.png)
    1. `PLANNED` Planned for deployment, but not yet deployed. It exists only as a record in Colly for planning purposes.
    2. `FREE` The environment is successfully deployed in the cloud but is not used by anyone; it is ready for use and not scheduled for usage.
    3. `IN_USE` The environment is successfully deployed in the cloud and is being used by a specific team for specific purposes.
    4. `RESERVED` The environment is successfully deployed in the cloud and reserved for use by a specific team, but is not currently in use.
    5. `DEPRECATED` The environment is not used by anyone, and a decision has been made to delete it.
  - Should it be extendable?

- [ ] `role`

  - There is already `type`, which is based on labels set by the Cloud Passport Discovery CLI.
  - Discuss with Pankratov to clarify whether this attribute should be computed by Colly (and if so, based on what criteria), or if it should be user-defined.
  - Should it be extendable?

- [ ] `syncInterval`, `syncStatus.lastSyncResult`, `syncStatus.lastSyncCompletedAt`
  - поправить термин cluster info update
  - принудительный синк?

- [ ] `team` or `teams`? `owner` or `owners`?
  - `owners`, `teams` are strings

- [+] Each POST in the API will result in a separate commit

- [ ] Product/Project SDs
  - Mapping of SD type to SD name is specified in the configuration:

    ```yaml
    solutionDescriptors:
      <sd-type>:
        - <sd-name-regexp>
    ```

  - The configuration is a deployment parameter of the Colly application
  - Default value:

      ```yaml
      solutionDescriptors:
        product:
          - .*product.*
        project:
          - .*project.*
        infra:
          - .*infra.*
      ```

- [+] `id` is `uuid`; `name` is `<environment-name>`
