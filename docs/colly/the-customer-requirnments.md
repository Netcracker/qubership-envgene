# API Enhancement of according to the Customer requirements

- [API Enhancement of according to the Customer requirements](#api-enhancement-of-according-to-the-customer-requirements)
  - [Environment](#environment)
  - [Namespace](#namespace)
  - [Cluster](#cluster)
  - [Colly instance](#colly-instance)
  - [To discuss](#to-discuss)
  - [To implement](#to-implement)

## Environment

| Colly Attribute  | Attribute Type                                                | Description                                                                                                                                    |
|------------------|---------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`           | string                                                        | Environment name, cannot be changed after creation                                                                                             |
| `status`         | enum [`PLANNED`, `FREE`, `IN_USE`, `RESERVED`, `DEPRECATED`]  | Current status of the Environment                                                                                                              |
| `role`           | enum [`Dev`, `QA`, `Project CI`, `SaaS`, `Joint CI`, `Other`] | Defines usage role of the Environment                                                                                                          |
| `teams`          | list of strings                                               | Teams assigned to the Environment. If there are several teams, their names are separated by commas.                                            |
| `owners`         | list of strings                                               | People responsible for the Environment. If there are several, their names are separated by commas.                                             |
| `productSDs`     | list of strings                                               | List of Solution Descriptors with type `product` in `<name>:<version>` notation, which are currently successfully deployed in this Environment |
| `projectSDs`     | list of strings                                               | List of Solution Descriptors with type `project` in `<name>:<version>` notation, which are currently successfully deployed in this Environment |
| `infraSDs`       | list of strings                                               | List of Solution Descriptors with type `infra` in `<name>:<version>` notation, which are currently successfully deployed in this Environment   |
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

| Colly Attribute                           | Attribute Type | Description                                                                                                                                                                                                    |
|-------------------------------------------|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`                                    | string         | Cluster name, cannot be changed after creation                                                                                                                          |
| `clusterInfoUpdateStatus.lastResult`      | string         | Determines the information update status for cluster: if at least one object from the cluster was successfully read, the information update is considered successful                                            |
| `clusterInfoUpdateStatus.lastCompletedAt` | string         | Time of the last successful update information from the cluster                                                                                                          |

## Colly instance

| Colly Attribute                    | Attribute Type   | Description                                                   |
|------------------------------------|----------------- |---------------------------------------------------------------|
| `clusterInfoUpdateStatusInterval`  | string, duration | Period of synchronization with the cluster in ISO 8601 format |

## To discuss

- [ ] Product/Project SDs
  - Mapping of SD type to SD name is specified in the Colly deployment parameters:

    ```yaml
    solutionDescriptors:
      <sd-type>:
        - <sd-name-regexp>
    ```

  - Default value:

      ```yaml
      solutionDescriptors:
        product:
          - (?i)product
        project:
          - (?i)project
        infra:
          - (?i)infra
          - (?i)platform
      ```

- [ ] `status`

  - Propose ![env-state-machine.drawio.png](/docs/images/env-state-machine.drawio.png)
    1. `PLANNED` Planned for deployment, but not yet deployed. It exists only as a record in Colly for planning purposes.
    2. `FREE` The Environment is successfully deployed in the cloud but is not used by anyone; it is ready for use and not scheduled for usage.
    3. `IN_USE` The Environment is successfully deployed in the cloud and is being used by a specific team for specific purposes.
    4. `RESERVED` The Environment is successfully deployed in the cloud and reserved for use by a specific team, but is not currently in use.
    5. `DEPRECATED` The Environment is not used by anyone, and a decision has been made to delete it.
  - OQ:
    1. What are the cases?
    2. Should it be extendable?
    3. What is `to be deprecated`? Why do we not have `deprecated`, `deleted`, or `not used` states?
    4. Do we need `MIGRATING` (meaning the upgrade is in progress)?

- [ ] `clusterInfoUpdateInterval`, `clusterInfoUpdateStatus.result`, `clusterInfoUpdateStatus.lastSuccessDate`

  - OQ:
    1. What are the cases?
    2. Should Colly support a forced clusterInfoUpdate — not on a schedule, but triggered by a user request?

- [ ] `type`

  - `type`  is based on labels set by the Cloud Passport Discovery CLI.
  - OQ:
    1. This attribute should be computed by Colly (and if so, based on what criteria), or if it should be user-defined (Discuss with Pankratov)

- [ ] Lock
  - The lock must answer the following questions:
    - Status: locked or not locked
    - Who locked it: free-form string
    - Reason for locking: free-form string
    - When it was locked: timestamp
    - When it will be unlocked: date
  - Required interfaces:
    - Set/remove lock on the environment
    - Force sync lock status from Git (can be implemented later)
  - Only a Colly admin can lock through the UI; users cannot
  - OQ:
    1. Should locks be defined by inventory backend?
    2. Who, when and why lock/unlock
    3. What are the cases from SSP?

- [ ] Last Deploy Date
  - Last Deploy Date is the time of completion of the most recent deployment operation on the environment, regardless of the result or type (SD, DD).

- [ ] Last login date
  - OQ:
    1. Do we keep this parameter as is?

- [+] `role`

  - Should it be extendable?
    - Currently, `role` are extended via deployment parameters
  - A separate interface to provide the list of roles is needed

- [+] `team` or `teams`? `owner` or `owners`?
  - `owners`, `teams` are lists

- [+] Each POST in the API will result in a separate commit

- [+] `id` is `uuid`; `name` is `<environment-name>`

## To implement

1. Change environment attributes
   1. `team`(string) -> `teams`(list of strings)
   2. `owner`(string) -> `owners`(list of strings)
2. Add deployment parameter to extend `role` valid values
3. Implement an interface that returns the list of `role` valid values (Low priority)
4. Return the Colly API version in the X-API-Version header of all responses
