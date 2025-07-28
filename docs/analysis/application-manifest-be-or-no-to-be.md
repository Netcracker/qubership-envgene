# Application Manifest. Be or not to be?

## Problem Statement

1. Transfer of Build-Time Artifact Parameters to Helm Charts

    For deployment of applications via Helm, it is necessary to pass dynamic artifact (Docker image, ZIP/JAR Maven artifact) parameters (names, versions, groups, digests, ...) into the Helm values

    These parameters are determined only at build time, while the build and deployment processes may be separated in time, which requires a mechanism for transferring and maintaining consistency between artifacts and the Helm charts.

2. Dependency of Helm Values Structure on Helm Chart Structure

    The structure of Helm values depends on the structure of the application's Helm charts (the composition of Helm charts and their relationships). To generate service parameters (including performance parameters), the configuration management must have information about the structure of the application's Helm charts.

## Proposed approaches

1. Generation of Helm values at the application build stage

    During the application build, a Helm values file containing artifact parameters is generated. This file is then used during the Helm chart build, becoming part of the chart. It is delivered as part of the chart and used during the rendering of the Helm chart.

    ![no-application-manifest.drawio.png](/docs/images/no-application-manifest.drawio.png)

    Pros:
      - No need to handle artifact parameters in CM
      - No additional entity introduction

    Cons:
      - If artifact is rebuilt, Helm chart needs to be updated
      - Does not solve the problem of dependency of deployment parameters on Helm chart structure: CM does not provide the ability to manage service-level parameters

2. Manual update of Helm values

    Manually updating Helm values at the build stage.

    Pros:
      - Does not require additional automation or tooling
      - No additional entity introduction

    Cons:
      - Error-prone and time-consuming
      - Does not solve problem of dependency of deployment parameters on Helm chart structure: CM does not provide the ability to manage service-level parameters

3. Generation of Application Manifest

    Using the Application Manifest as a single source of truth for application components (including Helm charts, their structure, dynamic artifact's parameters).
    The Application Manifest is created at the application build stage, published to a repository, and used to generate Helm values. The configuration management generates Helm values as part of the effective set.

    ![application-manifest.drawio.png](/docs/images/application-manifest.drawio.png)

    Pros:
      - Solves both problems:
        - Transfer of Build-Time Artifact Parameters to Helm Charts
        - Dependency of Deployment Parameters on Helm Chart Structure
      - Provides ability to extend set of transmitted attributes to support additional scenarios. For example, passing Helm value schemas or baseline performance parameters.

    Cons:
      - Introduction of Application Manifest entity that needs to be maintained across different tools (Argo, Pipelines, EnvGene, ADG, etc.) and scenarios

<!-- 4. Kustomize / Helmfile

    Not applicable to the problem being solved, as these tools are intended for configuration modification mechanisms and aggregation from different sources, not for transferring configuration.

1. ArgoCD Image Updater

    Using tools such as ArgoCD Image Updater to automatically update Docker image versions in the Helm values file based on new image tags detected in the container registry.

    Cons:
      - Limited to Docker images; does not support other artifact types such as Maven artifacts
      - Does not address the dependency of deployment parameters on the Helm chart structure

2. Renovate Bot / Dependabot

  Is an implementation of the "Generation of Helm values at the application build stage" approach -->

### "Pros and Cons" Table

| Approach                              | Pros                                                                                                 | Cons                                                                                                   |
|---------------------------------------|------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| Helm values generation at build stage | 1. No need to handle artifact parameters in CM<br>2. No additional entity introduction | 1. If artifact is rebuilt, Helm chart needs to be updated<br>2. CM does not provide the ability to manage service-level parameters |
| Manual update of Helm values          | 1. Does not require additional automation or tooling<br>2. No additional entity introduction | 1. Error-prone and time-consuming<br>2. CM does not provide the ability to manage service-level parameters |
| Application Manifest generation       | 1. Solves both problems <br>2. Provides ability to extend set of transmitted attributes to support additional scenarios. For example, passing Helm value schemas or baseline performance parameters. | 1. Introduction of Application Manifest entity that needs to be maintained across different tools (Argo, Pipelines, EnvGene, ADG, etc.) and scenarios |
