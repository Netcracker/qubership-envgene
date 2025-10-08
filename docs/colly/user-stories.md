# Colly User Stories

- [Colly User Stories](#colly-user-stories)
  - [Glossary](#glossary)
  - [Stories](#stories)
    - [US-1 As a TM I want to know about the last deployment operation performed on Environment](#us-1-as-a-tm-i-want-to-know-about-the-last-deployment-operation-performed-on-environment)
    - [US-2 As a TM I want to know about the last clean deployment operation performed on Environment](#us-2-as-a-tm-i-want-to-know-about-the-last-clean-deployment-operation-performed-on-environment)
    - [US-3 As a TM I want to know about the current state of installed SDs on Environment at the moment](#us-3-as-a-tm-i-want-to-know-about-the-current-state-of-installed-sds-on-environment-at-the-moment)
    - [US-4 As a DEV I want to know the list of applications in `app:ver` notation that are installed on Environment at the moment](#us-4-as-a-dev-i-want-to-know-the-list-of-applications-in-appver-notation-that-are-installed-on-environment-at-the-moment)

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

### US-1 As a TM I want to know about the last deployment operation performed on Environment

**Required information:**

1. Deployment operation completion time
2. Deployment operation completion result (SUCCESS/FAIL)
3. Deployment operation mode (CLEAN_INSTALL/ROLLING_UPDATE)
4. List of Solution Descriptors being installed in `app:ver` format

**Information source:**

1. ConfigMap `sd_versions` from cluster Namespace

### US-2 As a TM I want to know about the last clean deployment operation performed on Environment

**Required information:**

1. Clean deployment operation completion time
2. Clean deployment operation completion result

**Information source:**

1. ConfigMap `sd_versions` from cluster Namespace

### US-3 As a TM I want to know about the current state of installed SDs on Environment at the moment

**Required information:**

1. List of Solution Descriptors in `app:ver` format
2. Solution Descriptor type

**Information source:**

1. ConfigMap `sd_versions` from cluster Namespace

### US-4 As a DEV I want to know the list of applications in `app:ver` notation that are installed on Environment at the moment

**Information source:** configuration map `versions` from cluster Namespace
