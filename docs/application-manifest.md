# Application Manifest PoC

## Table of Contents

- [Application Manifest PoC](#application-manifest-poc)
  - [Table of Contents](#table-of-contents)
  - [Goals](#goals)
  - [Limitation](#limitation)
  - [Requirements](#requirements)
  - [Open questions](#open-questions)
  - [Use Cases](#use-cases)
  - [Proposed Approach](#proposed-approach)
    - [Option 1.1 Application Manifest with plugins](#option-11-application-manifest-with-plugins)
    - [Option 1.2 Application Manifest without plugins](#option-12-application-manifest-without-plugins)
    - [Option 1.3 Application Manifest without service](#option-13-application-manifest-without-service)
    - [Option 2 No Application Manifest](#option-2-no-application-manifest)
  - [MoMs](#moms)
    - [09.06](#0906)
    - [PoC](#poc)

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
4. Effective Set generation must not require processing application artifacts
   1. EnvGene must generate Effective Set using only EnvGene Environment Instance and Application Manifest
5. Effective Set generation for an Environment should take no more than 30 seconds
6. Application Manifest should be based CycloneDX specification. Alternative formats may be considered
7. Application Manifest must be generated via dedicated CLI tool
8. Application Manifest must be generated at the application build stage
9. Application Manifest build must use the "new builder's" input contract
10. The [Effective Set](https://github.com/Netcracker/qubership-envgene/blob/feature/es_impovement_step_2/docs/calculator-cli.md#effective-set-v20) structure should remain unchanged

## Open questions

1. Which Helm chart structures should be supported within this PoC?
   1. One app chart per application
   2. Multiple app charts per application
   3. One non-app chart per application
   4. Multiple non-app charts per application
   5. Xue-xue (???)
2. Should the Application Manifest be compatible with other deployers?
3. Should deploying a 3rd-party Application (Helm chart) require an App manifest??
4. Should profile overrides allow setting parameters not present in the baseline profile?
   1. As an application owner, I want to restrict the set of configurable performance parameters to prevents users from introducing unsupported configurations.
5. Should CM provide access to baseline profiles?
   1. As a solution configurator, I need to modify performance parameters while seeing baseline values to prevent context switching

## Use Cases

1. Argo Deployment
   1. Deployment of a Qubership application
   2. Deployment of a 3rd-party application
   3. Deployment of a Solution of Qubership applications
   4. Deployment of a Solution of 3rd-party applications
   5. Deployment of a mixed group of 3rd-party and Qubership applications
2. Effective Set Calculation by Envgene
   1. Effective set calculation for a Qubership application
   2. Effective set calculation for a 3rd-party application
   3. Effective set calculation for a Solution of Qubership applications
   4. Effective set calculation for a Solution of 3rd-party applications
   5. Effective set calculation for a mixed Solution of 3rd-party and Qubership applications

## Proposed Approach

### Option 1.1 Application Manifest with plugins

1. Plugins (CDN, sample repo, smart plug) are described as separate component type
2. No resource profile baseline exists. Performance parameters are defined in the Helm chart values

![application-manifest-model-with-plugins.drawio.png](/docs/images/application-manifest-model-with-plugins.drawio.png)

[Application Manifest with Plugins JSON schema](/schemas/application-manifest-with-plugins.schema.json)

### Option 1.2 Application Manifest without plugins

1. Plugins (CDN, sample repo, smart plug) are described as services. They are not classified as a separate component type
2. No resource profile baseline exists. Performance parameters are defined in the Helm chart values

![application-manifest-model-without-plugins.drawio.png](/docs/images/application-manifest-model-without-plugins.drawio.png)

[Application Manifest without Plugins JSON schema](/schemas/application-manifest-without-plugins.schema.json)

QIP Example:

![application-manifest-model-with-plugins.drawio.png](/docs/images/qip-application-manifest-without-plugins.drawio.png)

[QIP Application Manifest example](/examples/application-manifest-qip-without-service.json)

### Option 1.3 Application Manifest without service

1. No service component exists
2. No resource profile baseline exists. Performance parameters are defined in the Helm chart values

![application-manifest-model-without-service.png](/docs/images/application-manifest-model-without-service.png)

[Application Manifest without Plugins JSON schema](/schemas/application-manifest-without-service.schema.json)

QIP Example:

![application-manifest-model-with-plugins.drawio.png](/docs/images/qip-application-manifest-without-service.drawio.png)

[QIP Application Manifest example](/examples/application-manifest-qip.json)

### Option 2 No Application Manifest

Centralized values.yaml generation during CI/CD that dynamically links all dependencies (Helm charts, images, libraries) before deployment.

![application-manifest-model-with-plugins.drawio.png](/docs/images/qip-application-manifest-without-service.drawio.png)

## MoMs

### 09.06

1. Since the deployer does not process plugin types (smartplug, sample repo, CDN) separately, there is no need to include them in SBOM. They can be described either as a Service object or a Helm chart (see item 2)
2. The necessity of a separate Service object is questionable. We need to examine QIP examples with and without them
3. Should deployment of a 3rd-party Helm chart require an Application Manifest?
4. No need for Resource Profile Baseline? Performance parameters can be described as values in the Helm chart
5. Consider early binding of the Helm chart and artifacts (Docker image, Helm library, ZIP, Spar artifacts) during the build. Generate Helm chart values from parameters describing the artifacts (e.g., GAV coordinates) using **Image Updater** or **Image Streams**
6. No need for AppDefs — G and A are static during publication. The application name (used SD) must match the artifact ID
7. RegDefs are required to describe the coordinates and access method to the registry

### PoC

![application-manifest-2.drawio.png](/docs/images/poc.png)
