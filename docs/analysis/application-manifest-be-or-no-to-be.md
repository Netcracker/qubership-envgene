# Application Manifest in Deployment cases: To Be or Not To Be?

## Problem Statement

Application deployment and calculation of deployment parameters require a specific object — the Deployment Descriptor, which is not available in open source. в данный момент

It is necessary to:

1. Provide deployment of an individual application in Qubership
2. Consider the possibility of substituting the Deployment Descriptor in deployment cases

ворнинг Delivery scenarios are not considered сейчас
  деливери сценарий - возможность доставить приложения на нужный энв

## Challenges  

1. Passing Build-Time Artifact Parameters to Helm Charts

    When deploying applications with Helm, it is necessary to provide artifact's dynamic parameters (such as Docker image names, versions, Maven artifact coordinates, etc.) to Helm values.

    These parameters are determined only at build time, while the build and deployment processes may be separated in time, which requires a mechanism for transferring and maintaining consistency between artifacts and the Helm charts.

2. Helm Values Structure Depends on Helm Chart Structure

    The structure of Helm values is determined by the structure of the application's Helm charts (how charts are composed and related). To generate service parameters (including performance parameters), configuration management needs to know the structure of the application's Helm charts.

3. Multiple Helm Charts in a Single Application Deployment

    An application is an atomic deployment unit. If an application consists of several Helm charts, the deployer needs an object that either contains these charts or references them.

## Proposed Approaches

### 1. Manual Update of Helm Values

    Manually update Helm values during the build or deploy process

    Pros:
      - No extra automation or tooling required
      - No new entities introduced
      - This approach is used in the industry

    Cons:
      - Error-prone and time-consuming

  ![no-application-manifest-manual.drawio.png7u](/docs/images/no-application-manifest-manual.drawio.png)  

### 2. Generate Helm Values at Application Build Time

    - During the application build, generate a Helm values file with artifact parameters. This file is then included in the Helm chart build and delivered as part of the chart, to be used during rendering. (Dynamic artifact parameters are set into Helm charts as Helm values during the chart build)

    - Changes to the application's Docker images are applied by Argo Image Updater

    - Per-service parameters in a structure aligned with the Helm chart are set by the user via CM

    - All application Helm charts have the same structure — one umbrella chart with child charts

    - During solution deployment, the SD is used, which points to the Helm charts

  ![no-application-manifest.drawio.png](/docs/images/no-application-manifest.drawio.png)

    Pros:
      - No new entities introduced
      - This approach is used in the industry

    Cons:
      - A procedure for updating dynamic parameters is required
        - There is no Argo Image Updater for Maven artifacts
      - Restrictions on the structure of the Helm chart
      - Delivery process may become more complex and needs additional consideration

### 3. External Application Metadata Storage

    - Use an external storage (e.g., S3, DB, Git, Vault, etc.) to store information about application components and their metadata.
    Metadata is saved at build time and used during deployment parameter calculation and deployment.

    - Changes to the application's images are applied by Argo

  ![no-application-manifest-storage.drawio.png](/docs/images/no-application-manifest-storage.drawio.png)

    Pros:
      - This approach is used in the industry

    Cons:
      - Delivery process may become more complex and needs additional consideration

### 4. Application Manifest Generation

    Use the Application Manifest as a single source of truth for application components (including Helm charts, their structure, and dynamic artifact parameters).
    The Application Manifest is created at build time, published to a repository, and used to generate Helm values. Configuration management generates Helm values as part of the effective set.

  ![application-manifest.drawio.png](/docs/images/application-manifest.drawio.png)

    Pros:
      - Solves all three problems
      - Extendable to support new Configuration Management scenarios (e.g., passing Helm value schemas or baseline performance parameters)

    Cons:
      - Introduces a new entity that must be maintained across different tools (Argo, Pipelines, EnvGene, delivery tools, etc.) and scenarios
      - No direct analogs found in the industry
      - no 3rd party Helm Chart deployment without Application Manifest

#### Application Manifest Structure

Application Manifest — это структурированный, версионированный документ, который служит единым источником истины для описания компонентов приложения и их метаданных.

      - Основан на спецификации CycloneDX
      - Включает компоненты различных типов, таких как:
        - application/vnd.qubership.service — абстрактные сервисы
        - application/vnd.docker.image — Docker образы
        - application/vnd.qubership.helm.chart — Helm чарты


    1. Plugins (CDN, sample repo, smart plug) are described as services. They are not classified as a separate component type
    2. No resource profile baseline exists. Performance parameters are defined in the Helm chart values
    3. The service list is formed according to the principle - **service for each `service` component**
    4. There are two types of dependencies between components:
      1. dependsOn - For describing external dependencies (logical links), where a component requires another component to function but does not physically include it.
      2. includes - For describing the physical composition of a component, when a parent artifact includes child components.

![application-manifest-model-without-plugins.drawio.png](/docs/images/application-manifest-model.drawio.png)

[Application Manifest JSON schema](/schemas/application-manifest.schema.json)

QIP Example:

![application-manifest-model-with-plugins.drawio.png](/docs/images/qip-application-manifest.drawio.png)

[QIP Application Manifest example](/examples/application-manifest-qip.json)

### Pros and Cons Table

| Approach                              | Pros                                                                                                 | Cons                                                                                                   |
|----------------------------------------|------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| Helm values generation at build stage  | 1. No need to handle artifact parameters in CM<br>2. No additional entity introduction               | 1. If artifact is rebuilt, Helm chart needs to be updated<br>2. CM does not provide the ability to manage service-level parameters |
| Manual update of Helm values           | 1. Does not require additional automation or tooling<br>2. No additional entity introduction         | 1. Error-prone and time-consuming<br>2. CM does not provide the ability to manage service-level parameters |
| External Application Metadata Storage  | 1. Solves all 3 problems<br>2. Approach is used in the industry                                         | 1. Requires introducing a new system (metadata storage)<br>2. Delivery process may become more complex and needs additional consideration |
| Application Manifest generation        | 1. Solves all 3 problems<br>2. Easily extendable to support new scenarios (e.g., passing Helm value schemas or baseline performance parameters) | 1. Introduces Application Manifest entity that must be maintained across different tools (Argo, Pipelines, EnvGene, ADG, etc.) and scenarios<br>2. No direct industry analogs |
