# Artifact-searcher

## Table of Contents

1. [Performance environment variables](#performance-environment-variables)
2. [Authentication](#authentication)
3. [Supported data models](#supported-data-models)

---

## Performance environment variables

| name                      | default                  | description                                                                                          |
|---------------------------|--------------------------|------------------------------------------------------------------------------------------------------|
| `TCP_CONNECTION_LIMIT`    | `100`                    | Maximum number of simultaneous TCP connections used to download artifacts from registries           |
| `DEFAULT_REQUEST_TIMEOUT` | `30`                     | Default request timeout in seconds for registry requests                                             |
| `WORKSPACE`               | `<system.temp.dir>/zips` | Local workspace directory used to store downloaded artifact ZIPs                                     |

---

## Authentication

Artifact-searcher supports **Basic Authentication (username/password)** for registries defined using **Registry Definition v1**.

Support for **Registry Definition v2** is **TBD**.


## Supported data models

### Registry definition

Artifact-searcher supports artifact definitions with following structure:

```yaml
# Application / Artifact definition
name: my-app
groupId: com.example
artifactId: my-app-artifact
registry:
  name: my-maven-registry
  credentialsId: my-credentials
  mavenConfig:
    repositoryDomainName: repo.example.com
    targetSnapshot: snapshots
    targetStaging: staging
    targetRelease: releases

