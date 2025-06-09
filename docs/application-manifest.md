# Application Manifest PoC

## Table of Contents

- [Application Manifest PoC](#application-manifest-poc)
  - [Table of Contents](#table-of-contents)
  - [Goals](#goals)
  - [Requirements](#requirements)
  - [Open questions](#open-questions)
  - [Proposed Approach](#proposed-approach)
    - [QIP Example](#qip-example)
    - [PoC](#poc)

## Goals

1. Develop Application Manifest design sufficient for the following:
   1. Qubership application deployment via ArgoCD
   2. Effective Set calculation via EnvGene
2. The application manifest should solve the following problems:
   1. Application component typing
   2. Service list formation for deployment context
   3. The need to download application artifacts for Effective Set calculation
3. Develop a CLI tool for Application Manifest generation
4. Perform Qubership application deployment using the Application Manifest

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

## Proposed Approach

![application-manifest-1.drawio.png](/docs/images/application-manifest-1.drawio.png)

[Application Manifest JSON schema](/schemas/application-manifest.schema.json)

### QIP Example

![application-manifest-1.drawio.png](/docs/images/application-manifest-3.drawio.png)

[QIP Application Manifest example](/examples/application-manifest-qip.json)

### PoC

![application-manifest-2.drawio.png](/docs/images/application-manifest-2.drawio.png)
