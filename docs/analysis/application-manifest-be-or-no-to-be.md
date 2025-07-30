# Application Manifest: To Be or Not To Be?

## Goals

1. Provide deployment of an individual application in Qubership
2. Deployment Descriptor substitution in deployment cases

## Limitation

1. Delivery scenarios are not considered

## Problem Statement

1. Passing Build-Time Artifact Parameters to Helm Charts

    When deploying applications with Helm, it is necessary to provide artifact's dynamic parameters (such as Docker image names, versions, Maven artifact coordinates, etc.) to Helm values.

    These parameters are determined only at build time, while the build and deployment processes may be separated in time, which requires a mechanism for transferring and maintaining consistency between artifacts and the Helm charts.

2. Helm Values Structure Depends on Helm Chart Structure

    The structure of Helm values is determined by the structure of the application's Helm charts (how charts are composed and related). To generate service parameters (including performance parameters), configuration management needs to know the structure of the application's Helm charts.

3. Multiple Helm Charts in a Single Application Deployment

    An application is an atomic deployment unit. If an application consists of several Helm charts, the deployer needs an object that either contains these charts or references them.

## Proposed Approaches

1. Manual Update of Helm Values

    Manually update Helm values during the build or deploy process.

    Pros:
      - No extra automation or tooling required
      - No new entities introduced
      - This approach is used in the industry

    Cons:
      - Error-prone and time-consuming

2. Generate Helm Values at Application Build Time

    - During the application build, generate a Helm values file with artifact parameters. This file is then included in the Helm chart build and delivered as part of the chart, to be used during rendering. (Dynamic artifact parameters are set into Helm charts as Helm values during the chart build)

    - Changes to the application's Docker images are applied by Argo Image Updater

    - Per-service parameters in a structure aligned with the Helm chart are set by the user via CM

    - All application Helm charts have the same structure — one umbrella chart with child charts

    - During solution deployment, the SD is used, which points to the Helm charts

    ![no-application-manifest.drawio.png](/docs/images/no-application-manifest.drawio.png)

    Pros:
      - No new entities introduced

    Cons:
      - A procedure for updating dynamic parameters is required
        - There is no Argo Image Updater for Maven artifacts
      - Restrictions on the structure of the Helm chart
      - Delivery process may become more complex and needs additional consideration
      - This approach is used in the industry

3. External Application Metadata Storage

    - Use an external storage (e.g., S3, DB, Git, Vault, etc.) to store information about application components and their metadata.
    Metadata is saved at build time and used during deployment parameter calculation and deployment.

    - Changes to the application's images are applied by Argo

    ![no-application-manifest-storage.drawio.png](/docs/images/no-application-manifest.drawio.png)

    Pros:
      - Solves all three problems
      - This approach is used in the industry

    Cons:
      - Requires introducing a new system
      - Delivery process may become more complex and needs additional consideration

4. Application Manifest Generation

    Use the Application Manifest as a single source of truth for application components (including Helm charts, their structure, and dynamic artifact parameters).
    The Application Manifest is created at build time, published to a repository, and used to generate Helm values. Configuration management generates Helm values as part of the effective set.

    ![application-manifest.drawio.png](/docs/images/application-manifest.drawio.png)

    Pros:
      - Solves all three problems
      - Extendable to support new scenarios (e.g., passing Helm value schemas or baseline performance parameters)

    Cons:
      - Introduces a new entity that must be maintained across different tools (Argo, Pipelines, EnvGene, delivery tools, etc.) and scenarios
      - No direct analogs found in the industry
      - no 3rd party Helm Chart deployment without Application Manifest

<!-- 4. Kustomize / Helmfile

    Not applicable to the problem being solved, as these tools are intended for configuration modification mechanisms and aggregation from different sources, not for transferring configuration.

1. ArgoCD Image Updater

    Using tools such as ArgoCD Image Updater to automatically update Docker image versions in the Helm values file based on new image tags detected in the container registry.

    Cons:
      - Limited to Docker images; does not support other artifact types such as Maven artifacts
      - Does not address the dependency of deployment parameters on the Helm chart structure

2. Renovate Bot / Dependabot

  Is an implementation of the "Generation of Helm values at the application build stage" approach -->

### Pros and Cons Table

| Approach                              | Pros                                                                                                 | Cons                                                                                                   |
|----------------------------------------|------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| Helm values generation at build stage  | 1. No need to handle artifact parameters in CM<br>2. No additional entity introduction               | 1. If artifact is rebuilt, Helm chart needs to be updated<br>2. CM does not provide the ability to manage service-level parameters |
| Manual update of Helm values           | 1. Does not require additional automation or tooling<br>2. No additional entity introduction         | 1. Error-prone and time-consuming<br>2. CM does not provide the ability to manage service-level parameters |
| External Application Metadata Storage  | 1. Solves all 3 problems<br>2. Approach is used in the industry                                         | 1. Requires introducing a new system (metadata storage)<br>2. Delivery process may become more complex and needs additional consideration |
| Application Manifest generation        | 1. Solves all 3 problems<br>2. Easily extendable to support new scenarios (e.g., passing Helm value schemas or baseline performance parameters) | 1. Introduces Application Manifest entity that must be maintained across different tools (Argo, Pipelines, EnvGene, ADG, etc.) and scenarios<br>2. No direct industry analogs |
