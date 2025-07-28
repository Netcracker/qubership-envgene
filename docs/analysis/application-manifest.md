# Application Manifest

## Table of Contents

- [Application Manifest](#application-manifest)
  - [Table of Contents](#table-of-contents)
  - [Goals](#goals)
  - [Limitation](#limitation)
  - [Requirements](#requirements)
  - [Open questions](#open-questions)
  - [Use Cases](#use-cases)
  - [Proposed Approach](#proposed-approach)
    - [Option 1.1 Application Manifest with plugins](#option-11-application-manifest-with-plugins)
    - [Option 1.2 Application Manifest without service](#option-12-application-manifest-without-service)
    - [Option 1.3 Application Manifest without plugins](#option-13-application-manifest-without-plugins)
    - [Option 2 No Application Manifest](#option-2-no-application-manifest)
    - [Application Manifest Build CLI](#application-manifest-build-cli)
  - [MoMs](#moms)
    - [09.06](#0906)
    - [16.06](#1606)
    - [17.06](#1706)
    - [23.06](#2306)

## Goals

1. Develop Application Manifest design sufficient for the following:
   1. Qubership application deployment via ArgoCD
   2. Effective Set calculation via EnvGene
2. The Application Manifest should solve the following problems:
   1. Application component typing
   2. Service list formation for deployment context
   3. The need to download application artifacts for Effective Set calculation
3. Develop a CLI tool for Application Manifest generation
4. Perform Qubership application deployment using the Application Manifest

## Limitation

1. Delivery cases are not considered
2. Migration procedure is not considered

## Requirements

1. Application Manifest must be open-source compatible
2. Application Manifest must be sufficient for application deploying by Argo
3. Application Manifest must be sufficient for calculate Effective Set by EnvGene
   1. without downloading application artifacts
4. Effective Set generation must not require processing application artifacts
   1. EnvGene must generate Effective Set using only EnvGene Environment Instance and Application Manifest
   2. Effective Set generation for an Environment should take no more than 30 seconds
5. Application Manifest should be based CycloneDX specification. Alternative formats may be considered
6. Application Manifest must be generated via dedicated CLI tool
7. Application Manifest must be generated at the application build stage
8. Application Manifest build should use the Builder's input contract

## Open questions

**Q1:** Which Helm chart structures should be supported in Application Manifest?

   1. One umbrella chart per application
   2. Multiple umbrella charts per application
   3. One non-umbrella chart per application
   4. Multiple non-umbrella charts per application

**A1:** All Helm chart structures used in practice within the Qubership (including those listed above) must be supported by the Application Manifest model

**Q2:** Should the Application Manifest be compatible with other deployers?

**A2:** No

**Q3:** Should deploying a 3rd-party Application (Helm chart) by Argo require an Application manifest?

**A3:** Yes

**Q4:** Is there enough information in a 3rd-party Application (Helm chart) to create an Argo Application CR?

**A4:**

**Q5:** Should profile overrides allow setting parameters not present in the baseline profile? As an application developer, I want to restrict the set of configurable performance parameters to prevents users from introducing unsupported configurations

**A5:** Performance parameters should be explicitly distinguished (e.g., via JSON schema). However, restricting their use is unnecessary

**Q6:** Should CM provide access to baseline profiles? As a environment configurator, I need to modify performance parameters while seeing baseline values to prevent context switching

**A6:** Yes

**Q7:** Should environment configurator be able to customize some parameters from [deploy-descriptor.yaml](https://github.com/Netcracker/qubership-envgene/blob/feature/es_impovement_step_2/docs/calculator-cli.md#version-20deployment-parameter-context-deploy-descriptoryaml) or [per service deployment-parameters.yaml](https://github.com/Netcracker/qubership-envgene/blob/feature/es_impovement_step_2/docs/calculator-cli.md#version-20deployment-parameter-context-per-service-deployment-parametersyaml) in **no Application Manifest** option?

**A7:** Yes, but these parameters must be validated for necessity.

**Q8:** Should the application developer be able to introduce their own types in the component type in the Application Manifest?

**A8:** Not at this time, but possibly in the future.

**Q9:** How are Helm app charts and Docker images created, built, and linked in mature open-source projects?

**A9:**

**Q10:** How are the version in Chart.yaml and the Helm chart artifact version in the OCI registry related? What should be specified in the version attribute of the `application/vnd.qubership.helm.chart` component for release and non-release versions?

**A10:**

**Q11:** How should the `application/vnd.docker.image` component be structured for a multi-architecture Docker image composed of multiple components linked by a manifest?

**A11:**

**Q12:** How to describe external dependencies in AM

**A12:**

## Use Cases

1. ArgoCD Deployment
   1. Deployment of a Qubership application
   2. Deployment of a 3rd-party application
   3. Deployment of a Solution of Qubership applications
   4. Deployment of a Solution of 3rd-party applications
   5. Deployment of a mixed group of 3rd-party and Qubership applications
2. Effective Set Calculation by EnvGene
   1. Effective set calculation for a Qubership application
   2. Effective set calculation for a 3rd-party application
   3. Effective set calculation for a Solution of Qubership applications
   4. Effective set calculation for a Solution of 3rd-party applications
   5. Effective set calculation for a mixed Solution of 3rd-party and Qubership applications
3. Application Helm chart structure:
   1. One umbrella chart per application
   2. Multiple umbrella charts per application
   3. One non-umbrella chart per application
   4. Multiple non-umbrella charts per application

## Proposed Approach

### Option 1.1 Application Manifest with plugins

1. Plugins (CDN, sample repo, smart plug) are described as separate component type
2. No resource profile baseline exists. Performance parameters are defined in the Helm chart values

![application-manifest-model-with-plugins.drawio.png](/docs/images/application-manifest-model-with-plugins.drawio.png)

[Application Manifest with Plugins JSON schema](/schemas/application-manifest-with-plugins.schema.json)

### Option 1.2 Application Manifest without service

1. No service component exists
2. No resource profile baseline exists. Performance parameters are defined in the Helm chart values
3. The service list is formed according to the principle - **service for each `Helm-chart` component**

![application-manifest-model-without-service.png](/docs/images/application-manifest-model-without-service.png)

[Application Manifest without Plugins JSON schema](/schemas/application-manifest-without-service.schema.json)

QIP Example:

![application-manifest-model-with-plugins.drawio.png](/docs/images/qip-application-manifest-without-service.drawio.png)

[QIP Application Manifest example](/examples/application-manifest-qip-without-service.json)

### Option 1.3 Application Manifest without plugins

1. Plugins (CDN, sample repo, smart plug) are described as services. They are not classified as a separate component type
2. No resource profile baseline exists. Performance parameters are defined in the Helm chart values
3. The service list is formed according to the principle - **service for each `service` component**
4. There are two types of dependencies between components:
   1. dependsOn - For describing external dependencies (logical links), where a component requires another component to function but does not physically include it.
   2. includes - For describing the physical composition of a component, when a parent artifact includes child components.

![application-manifest-model-without-plugins.drawio.png](/docs/images/application-manifest-model.drawio.png)

[Application Manifest without Plugins JSON schema](/schemas/application-manifest.schema.json)

QIP Example:

![application-manifest-model-with-plugins.drawio.png](/docs/images/qip-application-manifest.drawio.png)

[QIP Application Manifest example](/examples/application-manifest-qip.json)

### Option 2 No Application Manifest

Centralized Helm values generation during application build that dynamically links all dependencies (Helm charts, images, libraries) before Effective Set calculation and deployment.

In this option:

- Input for Argo: `app:ver` of the Helm chart or SD with elements referencing the `app:ver` Helm chart  
- Input for Envgene: SD with elements referencing the `app:ver` Helm chart  
- Envgene do not calculates per-service parameters, assuming such parameters are already present in values of Helm charts
- Helm values must contain at least
  - [deploy-descriptor.yaml](https://github.com/Netcracker/qubership-envgene/blob/feature/es_impovement_step_2/docs/calculator-cli.md#version-20deployment-parameter-context-deploy-descriptoryaml)
  - [per service deployment-parameters.yaml](https://github.com/Netcracker/qubership-envgene/blob/feature/es_impovement_step_2/docs/calculator-cli.md#version-20deployment-parameter-context-per-service-deployment-parametersyaml)

<!-- ![no-application-manifest-model.drawio.png](/docs/images/no-application-manifest-model.drawio.png) -->
![no-application-manifest.drawio.png](/docs/images/no-application-manifest.drawio.png)

### Application Manifest Build CLI

[Application Manifest Build CLI](/docs/analysis/application-manifest-build-cli.md)

## MoMs

### 09.06

1. Since the deployer does not process plugin types (smartplug, sample repo, CDN) separately, there is no need to include them in SBOM. They can be described either as a Service object or a Helm chart (see item 2)
2. The necessity of a separate Service object is questionable. We need to examine QIP examples with and without them
3. Should deployment of a 3rd-party Helm chart require an Application Manifest?
4. No need for Resource Profile Baseline? Performance parameters can be described as values in the Helm chart
5. Consider early binding of the Helm chart and artifacts (Docker image, Helm library, ZIP, Spar artifacts) during the build. Generate Helm chart values from parameters describing the artifacts (e.g., GAV coordinates) using **Image Updater** or **Image Streams**
6. No need for AppDefs — G and A are static during publication. The application name (used SD) must match the artifact ID
7. RegDefs are required to describe the coordinates and access method to the registry

### 16.06

1. Should user be able to customize some parameters from [deploy-descriptor.yaml](https://github.com/Netcracker/qubership-envgene/blob/feature/es_impovement_step_2/docs/calculator-cli.md#version-20deployment-parameter-context-deploy-descriptoryaml) or [per service deployment-parameters.yaml](https://github.com/Netcracker/qubership-envgene/blob/feature/es_impovement_step_2/docs/calculator-cli.md#version-20deployment-parameter-context-per-service-deployment-parametersyaml) ?

### 17.06

1. Need to choose between the following options: `Option 1.3: Application Manifest without plugins` and `Option 2: No Application Manifest`. Other options are rejected

### 23.06

1. `Option 1.3: Application Manifest without plugins` was chosen

<!-- ### PoC

![application-manifest-2.drawio.png](/docs/images/poc.png) -->
