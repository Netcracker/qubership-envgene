# Colly User Stories

- [Colly User Stories](#colly-user-stories)
  - [Glossary](#glossary)
  - [Stories](#stories)
    - [US-1 As a TM I want to know about the last deployment operation performed on the Environment](#us-1-as-a-tm-i-want-to-know-about-the-last-deployment-operation-performed-on-the-environment)
    - [US-2 As a TM I want to know about the last clean deployment operation performed on the Environment](#us-2-as-a-tm-i-want-to-know-about-the-last-clean-deployment-operation-performed-on-the-environment)
    - [US-3 As a TM I want to know about the current state of installed SDs on the Environment at the moment](#us-3-as-a-tm-i-want-to-know-about-the-current-state-of-installed-sds-on-the-environment-at-the-moment)
    - [US-4 As a DEV I want to know the list of applications in `app:ver` notation that are installed on the Environment at the moment](#us-4-as-a-dev-i-want-to-know-the-list-of-applications-in-appver-notation-that-are-installed-on-the-environment-at-the-moment)
    - [US-5 As a TM I want to know about the Environment](#us-5-as-a-tm-i-want-to-know-about-the-environment)
    - [US-6 As a TM I want to configure Environment attributes](#us-6-as-a-tm-i-want-to-configure-environment-attributes)
    - [US-7 As a TM I want to create the Environment](#us-7-as-a-tm-i-want-to-create-the-environment)
    - [US-9 As a TM I want to know how up-to-date the information discovered from the cluster is](#us-9-as-a-tm-i-want-to-know-how-up-to-date-the-information-discovered-from-the-cluster-is)
    - [US-10 As a TM, I want to know if the Environment is being used](#us-10-as-a-tm-i-want-to-know-if-the-environment-is-being-used)

## Glossary

**Namespace** - Kubernetes namespace that is part of Environment.
**Environment** - Logical entity that combines a set of Namespaces.
**The latest deployment operation on Environment** - the latest deployment operation by start time among all completed operations (regardless of result) on Namespaces that are part of Environment.
**Deployment operation mode** - CLEAN_INSTALL or ROLLING_UPDATE
**SD** - Solution Descriptor
**SD type** - PRODUCT_SD or PROJECT_SD. Solution Descriptors of different types are needed to group applications installed in an Environment that have the same lifecycle, particularly those that are installed and updated in a single deployment operation. For example, product applications and project applications are part of product and project Solution Descriptors respectively.
**DEV** - Developer
**TM** - Technical Manager

## Stories

### US-1 As a TM I want to know about the last deployment operation performed on the Environment

**Required information:**

1. Deployment operation completion time
2. Deployment operation completion result (`SUCCESS`/`FAIL`)
3. Deployment operation mode (`CLEAN_INSTALL`/`ROLLING_UPDATE`)
4. List of Solution Descriptors being installed in `app:ver`
5. Type Solution Descriptors being installed

**Notes:**

1. Solution Descriptors type is ...TBD...

### US-2 As a TM I want to know about the last clean deployment operation performed on the Environment

**Required information:**

1. Clean deployment operation completion time
2. Clean deployment operation completion result (`SUCCESS`/`FAIL`)

### US-3 As a TM I want to know about the current state of installed SDs on the Environment at the moment

**Required information:**

1. List of Solution Descriptors in `app:ver` format
2. Solution Descriptor type

### US-4 As a DEV I want to know the list of applications in `app:ver` notation that are installed on the Environment at the moment

### US-5 As a TM I want to know about the Environment

**Required information:**

1. ID
2. Type
3. Status
4. Owner name
5. Name of the team to which the Environment is allocated
6. List of namespaces included in the Environment
7. Environment description
8. Cluster name where the Environment is deployed

**Notes:**

1. The Environment ID is specified in the `<cluster-name>/<env-name>` notation

### US-6 As a TM I want to configure Environment attributes

**Required information:**

1. Type
2. Status
3. Owner name
4. Name of the team to which the Environment is allocated
5. Environment description

### US-7 As a TM I want to create the Environment

### US-9 As a TM I want to know how up-to-date the information discovered from the cluster is

**Required information:**

1. Result of the last discovery attempt from the cluster
2. Completion time of the last discovery operation from the cluster
3. Completion time of the last successfully completed discovery operation from the cluster
4. The interval at which discovery from the cluster is performed regularly

**Notes:**

1. The success criterion is that the cluster API responds to at least one of the requests during the discovery

### US-10 As a TM, I want to know if the Environment is being used

**Required information:**

1. The time of the last authorization in the applications that are part of the solution, performed via the IDP
