# Application Manifest in Deployment Cases: To Be or Not To Be?

## Problem Statement

To clarify, the topic of this discussion is not the Application Manifest itself, but finding a solution that will:

1. Enable application deployment in Qubership
2. Consider replacing the Deployment Descriptor (DD) in deployment scenarios

Currently, application deployment and deployment parameter calculation require a special object — the Deployment Descriptor — which is not available as open source.

The DD is used as both a deployment and delivery unit. In this discussion, we focus only on the deployment aspect; delivery scenarios are out of scope.

The lack of an open source DD alternative brings the following challenges:

## Challenges

1. Passing Build-Time Artifact Parameters to Helm Charts

    When deploying applications, we need to pass dynamic artifact parameters (like Docker image names, versions, Maven coordinates, etc.) to Helm values.

    These parameters are known at build time, but build and deployment can happen at different times. We need a way to transfer and keep these parameters in sync between artifacts and Helm charts.

    Example of such parameters currently used for deployment:

    ```yaml
    # docker image params 
    docker_digest: 4c7d5713761d9b119635d2e12276d0802f837b97ec5ce32aacd87d79a89faf20
    docker_registry: registry.qubership.org:10004
    docker_repository_name: cloud
    docker_tag: build21
    full_image_name: registry.qubership.org:10004/cloud/application-assembly-release-2024.3:build21
    # maven artifact params
    artifact:
      artifactId: application-configuration
      groupId: org.qubership.cloud
      version: release-2024.3-20240830.135742-build3
    maven_repository: https://registry.qubership.org/mvn.group
    ```

2. Resource Profile Baseline Processing

    Currently:
    - Resource profile baseline files are stored in the zip part of the application
    - EnvGene processes these parameters when calculating Helm values

    For this, EnvGene has to download the entire application, which leads to:
    - Increased time to calculate Helm values
    - The need to maintain a contract for resource profile baseline in Qubership applications

3. Helm Values Structure Depends on Helm Chart Structure

    The structure of Helm values depends on how the application's Helm charts are organized.
    To generate service parameters (mostly performance parameters), EnvGene must know the structure of the application's Helm charts.

    For example, the structure of service-level parameters is different for an app with a single umbrella chart and subcharts versus an app with multiple Helm charts.

4. Multiple Helm Charts in a Single Application Deployment

    An application is an atomic deployment unit. If it includes several Helm charts, the deployer needs an object that either contains or references all these charts.

## Proposed Approaches

Approaches that solve these problems and achieve the goals, including what is used in the industry:

### Option 1. Manual Update of Helm Values

In this approach:

- Helm values are updated manually during build or deploy
- No resource profile baseline; performance parameters are set in Helm chart values
- All application Helm charts have the same structure: one umbrella chart with child charts
- Input for Argo: `app:ver` of the Helm chart or SD referencing the `app:ver` Helm chart  
- Input for EnvGene: SD referencing the `app:ver` Helm chart  

Pros:

- No extra automation or tooling needed
- No entities introduced
- This approach is used in the industry

Cons:

- Error-prone and time-consuming
- Restrictions on Helm chart structure

  ![no-application-manifest-manual.drawio.png7u](/docs/images/no-application-manifest-manual.drawio.png)  

### Option 2. Generate Helm Values at Build Time and Store into Helm Chart

In this approach:

- Dynamic artifact parameters are set in Helm charts as Helm values during chart build by builder
- No resource profile baseline; performance parameters are set in Helm chart values
- All application Helm charts have the same structure: one umbrella chart with child charts
- Input for Argo: `app:ver` of the Helm chart or SD referencing the `app:ver` Helm chart  
- Input for EnvGene: SD referencing the `app:ver` Helm chart  
- EnvGene does not calculate service parameters, assuming they are already present in Helm chart values
- EnvGene allows the user to set service parameters in a structure matching the Helm chart
- To avoid rebuilding the Helm chart when Docker image versions change, Argo Image Updater is used to update images

![no-application-manifest.drawio.png](/docs/images/no-application-manifest.drawio.png)

Pros:

- No new entities introduced
- This approach is used in the industry

Cons:

- No Argo Image Updater for Maven artifacts
- Restrictions on Helm chart structure

### Option 3. Generate Helm Values at Build Time and Store into External Storage

In this approach:

- Use external storage (e.g., S3, Git, Vault, etc.) to store dynamic artifact parameters
- Dynamic artifact parameters are stored at build time by builder as Helm values
- Dynamic artifact parameters are used during deployment
- No resource profile baseline; performance parameters are set in Helm chart values
- All application Helm charts have the same structure: one umbrella chart with child charts
- Input for Argo: `app:ver` of the Helm chart or SD referencing the `app:ver` Helm chart  
- Input for EnvGene: SD referencing the `app:ver` Helm chart
- EnvGene does not calculate service parameters, assuming they are stored in external storage
- EnvGene allows the user to set service parameters in a structure matching the Helm chart

![no-application-manifest-storage.drawio.png](/docs/images/no-application-manifest-storage.drawio.png)

Pros:

- This approach is used in the industry

Cons:

- Restrictions on Helm chart structure

### Option 4. Application Manifest Generation

Application Manifest (AM) is a structured, versioned JSON that acts as a single source of truth for describing application components and their metadata. It is an open source alternative to the DD.

- Based on CycloneDX 1.6 specification
- Includes components of different types, such as:
  - `application/vnd.qubership.service` — abstract services
  - `application/vnd.docker.image` — Docker images
  - `application/vnd.qubership.helm.chart` — Helm charts

In this approach:

- Use the AM as the single source of truth for application components (including Helm charts, their structure, and dynamic artifact parameters)
- The AM is created at build time and published to a repository
- No resource profile baseline; performance parameters are set in Helm chart values
- Input for Argo: `app:ver` of the AM or SD referencing the `app:ver` AM
- Input for EnvGene: SD referencing the `app:ver` AM
- EnvGene calculates service parameters based on the AM
- EnvGene allows the user to set service parameters in a structure matching the Helm chart

![application-manifest.drawio.png](/docs/images/application-manifest.drawio.png)

Pros:

- Can be extended to support more configuration management scenarios (for example passing Helm value schemas)
- No restrictions on Helm chart structure

Cons:

- Introduces a new entity that must be maintained across different tools (Argo, Pipelines, EnvGene, delivery tools, etc.) and scenarios
- No 3rd party Helm chart deployment without AM generation
- No direct industry analogs

### Approaches comparison

| Approach                              | Pros                                                                                                 | Cons                                                                                                   |
|----------------------------------------|------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| 1. Manual update of Helm values |  1. No extra automation or tooling needed<br>2. No additional entity introduction<br>3. This approach is used in the industry | 1. Error-prone and time-consuming<br>2. Restrictions on Helm chart structure |

| 2. Generate Helm Values at Build Time and Store into Helm Chart  | 1. No new entities introduced<br>2. This approach is used in the industry | 1. No Argo Image Updater for Maven artifacts<br>2. Restrictions on Helm chart structure |

| 3. Generate Helm Values at Build Time and Store into External Storage | 1. This approach is used in the industry | 1. Restrictions on Helm chart structure |

| Option 4. Application Manifest Generation | 1. Can be extended to support more configuration management scenarios<br>2. No restrictions on Helm chart structure | 1. Introduces a new entity that must be maintained across different tools and scenarioss<br>2. No 3rd party Helm chart deployment without AM generation<br>3. No direct industry analogs |

### Application Manifest Structure

1. Plugins (CDN, sample repo, smart plug) are described as services. They are not classified as a separate component type
2. The service list is formed according to the principle: **service for each `service` component**
3. There are two types of dependencies between components:
   1. dependsOn - For describing external dependencies (logical links), where a component requires another component to function but does not physically include it.
   2. includes - For describing the physical composition of a component, when a parent artifact includes child components.

![/docs/images/application-manifest-model.drawio.png](/docs/images/application-manifest-model.drawio.png)

[Application Manifest JSON schema](/schemas/application-manifest.schema.json)

QIP Example:

![/docs/images/qip-application-manifest.drawio.png](/docs/images/qip-application-manifest.drawio.png)

[QIP Application Manifest example](/examples/application-manifest-qip.json)
