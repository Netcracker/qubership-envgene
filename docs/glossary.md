# Glossary

- [Glossary](#glossary)
  - [How to use this glossary](#how-to-use-this-glossary)
  - [Terms with one meaning](#terms-with-one-meaning)
  - [Terms with several meanings](#terms-with-several-meanings)
    - [Application](#application)
    - [Artifact](#artifact)
    - [Baseline](#baseline)
    - [Clean](#clean)
    - [Context](#context)
    - [Definition](#definition)
    - [Deployment Descriptor](#deployment-descriptor)
    - [External](#external)
    - [Macro](#macro)
    - [Merge mode](#merge-mode)
    - [Namespace name](#namespace-name)
    - [Override](#override)
    - [Parameters](#parameters)
    - [Pipeline](#pipeline)
    - [Profile](#profile)
    - [Registry](#registry)
    - [Repository](#repository)
    - [SBOM](#sbom)
    - [Side](#side)
    - [Template](#template)
    - [Version](#version)

This glossary lists EnvGene terms. It does not define them. Each entry links to the document that defines the
term, so a definition lives in one place only.

## How to use this glossary

A term with one meaning has a single link. A term with several meanings lists its senses, each with a short label, the
field or ADR where it appears, and a link. Decide which sense a listed word carries before you act on it.

A word gets a list of senses when it appears in the Decision or Consequences section of an ADR under `docs/adr/`, or
in the name of a field, and has more than one meaning. Two ADR numbers are shared by two files each, so ADRs are
cited with their topic, for example ADR-0009 (app chart). Both ADR-0009 and both ADR-0012 files have the status
Proposed.

## Terms with one meaning

- **AppDef** - see [Application Definition](/docs/envgene-objects.md#application-definition).
- **Application Definition** - see [Application Definition](/docs/envgene-objects.md#application-definition).
- **Application SBOM** - see [SBOM types](/docs/features/sbom.md#application-sbom).
- **`appregdef_config.yaml`** - see [`appregdef_config.yaml`](/docs/envgene-configs.md#appregdef_configyaml).
- **Artifact Definition** - see [Artifact Definition](/docs/envgene-objects.md#artifact-definition).
- **BG Domain** - see [BG Domain](/docs/envgene-objects.md#bg-domain).
- **BG Side Role** - see [Lifecycle in plain terms](/docs/features/blue-green-deployment.md#lifecycle-in-plain-terms).
- **BG State Files** - see [BG State Files](/docs/envgene-objects.md#bg-state-files).
- **BGD** - see [Blue-Green Deployment](/docs/features/blue-green-deployment.md).
- **`bgNsArtifacts`** - see [What a BG environment looks
  like](/docs/features/blue-green-deployment.md#what-a-bg-environment-looks-like).
- **Blue-Green Deployment** - see [Blue-Green Deployment](/docs/features/blue-green-deployment.md).
- **Calculator CLI** - see [Calculator CLI](/docs/features/calculator-cli.md).
- **Cleanup Context** - see [Cleanup Context](/docs/features/calculator-cli.md#version-20-cleanup-context).
- **Cloud** - see [Cloud](/docs/envgene-objects.md#cloud).
- **Cloud Passport** - see [Cloud Passport](/docs/envgene-objects.md#cloud-passport).
- **Cloud Template** - see [Cloud Template](/docs/envgene-objects.md#cloud-template).
- **Composite Structure** - see [Composite Structure](/docs/envgene-objects.md#composite-structure).
- **`config.yml`** - see [`config.yml`](/docs/envgene-configs.md#configyml).
- **Credential** - see [Credential](/docs/envgene-objects.md#credential).
- **Credential Reference** - see [Credential Reference](/docs/features/external-creds.md#credential-reference).
- **Credential Rotation** - see [Credential Rotation](/docs/features/cred-rotation.md).
- **Credential Template** - see [Credential Template](/docs/envgene-objects.md#credential-template).
- **`current_env`** - see [Template Macros](/docs/template-macros.md#jinja-macros).
- **Custom Params** - see [`CUSTOM_PARAMS`](/docs/instance-pipeline-parameters.md#custom_params).
- **DCL Repository** - see [No-CMDB v2](/docs/deployment-architecture.md#no-cmdb-v2).
- **DD** - see [Deployment Descriptor](#deployment-descriptor).
- **Definition Override** - see [Definition overrides](/docs/features/app-reg-defs.md#definition-overrides).
- **Delta SD** - see [Delta SD](/docs/features/sd-processing.md#delta-sd).
- **Deploy Plan** - see [Calculator command-line tool execution
  attributes](/docs/features/calculator-cli.md#calculator-command-line-tool-execution-attributes).
- **Deploy Postfix** - see [`useDeployPostfixAsNamespace`
  Handling](/docs/features/sd-processing.md#usedeploypostfixasnamespace-handling).
- **Deployer** - see [`deployer.yml`](/docs/envgene-configs.md#deployeryml), set per environment by
  `inventory.deployer`.
- **`deployer.yml`** - see [`deployer.yml`](/docs/envgene-configs.md#deployeryml).
- **Deployment Architecture** - see [Deployment architecture](/docs/deployment-architecture.md).
- **Deployment Parameter Context** - see [Deployment Parameter
  Context](/docs/features/calculator-cli.md#version-20-deployment-parameter-context).
- **`deployParameters`** - see [Deployment Parameter
  Context](/docs/features/calculator-cli.md#version-20-deployment-parameter-context).
- **Discovery Repository** - see [Discovery Pipeline Parameters](/docs/discovery-pipeline-parameters.md).
- **`e2eParameters`** - see [`e2eParameters`](/docs/e2e-parameters.md).
- **Effective Definition** - see [Overview](/docs/features/app-reg-defs.md#overview).
- **Effective Set** - see [Effective Set
  Structure](/docs/features/calculator-cli.md#version-20-effective-set-structure).
- **`envgeneNullValue`** - see [Credential](/docs/envgene-objects.md#credential).
- **Environment** - see [Environment Instance Objects](/docs/envgene-objects.md#environment-instance-objects).
- **Environment Credentials File** - see [Environment Credentials
  File](/docs/envgene-objects.md#environment-credentials-file).
- **Environment Instance** - see [Environment Instance Objects](/docs/envgene-objects.md#environment-instance-objects).
- **Environment Inventory** - see [env_definition.yml](/docs/envgene-configs.md#env_definitionyml).
- **Environment Specific ParameterSet** - see [Environment Specific
  ParameterSet](/docs/envgene-objects.md#environment-specific-parameterset).
- **Environment Specific Resource Profile Override** - see [Environment Specific Resource Profile
  Override](/docs/envgene-objects.md#environment-specific-resource-profile-override).
- **Environment Template** - see [Environment Template Objects](/docs/envgene-objects.md#environment-template-objects).
- **Environment Template Artifact** - see [Environment Template
  Objects](/docs/envgene-objects.md#environment-template-objects).
- **Environment Template SBOM** - see [SBOM types](/docs/features/sbom.md#environment-template-sbom).
- **ES** - see [Effective Set](/docs/features/calculator-cli.md#version-20-effective-set-structure).
- **ESO** - see [Parameter with ESO reference](/docs/features/external-creds.md#parameter-with-eso-reference).
- **`eso_support`** - see [`eso_support` attribute](/docs/features/external-creds.md#eso_support-attribute).
- **External Credential Context** - see [External Credential
  Context](/docs/features/calculator-cli.md#version-20-external-credential-context).
- **Full SD** - see [Full SD](/docs/features/sd-processing.md#full-sd).
- **Instance Pipeline** - see [Instance pipeline](/docs/envgene-pipelines.md#instance-pipeline).
- **Instance Repository** - see [Instance Repository Objects](/docs/envgene-objects.md#instance-repository-objects).
- **`integration.yml`** - see [`integration.yml`](/docs/envgene-configs.md#integrationyml).
- **Local mode** - see [Mode detection](/docs/features/credential-processing.md#mode-detection).
- **Namespace** - see [Namespace](/docs/envgene-objects.md#namespace).
- **Namespace Template** - see [Namespace Template](/docs/envgene-objects.md#namespace-template).
- **No-CMDB** - see [Deployment architecture](/docs/deployment-architecture.md).
- **Operation Type** - see [`OPERATION_TYPE`](/docs/instance-pipeline-parameters.md#operation_type).
- **ParameterSet** - see [Template ParameterSet](/docs/envgene-objects.md#template-parameterset).
- **Partial Generation** - see [Partial Generation](/docs/features/effective-set-generation.md#partial-generation).
- **Pipeline Parameter Context** - see [Pipeline Parameter
  Context](/docs/features/calculator-cli.md#version-20-pipeline-parameter-context).
- **Pipeline Type** - see [`PIPELINE_TYPE`](/docs/instance-pipeline-parameters.md#pipeline_type).
- **RegDef** - see [Registry Definition](/docs/envgene-objects.md#registry-definition).
- **Registry Definition** - see [Registry Definition](/docs/envgene-objects.md#registry-definition).
- **Resource Profile Override** - see [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override).
- **Runtime Parameter Context** - see [Runtime Parameter
  Context](/docs/features/calculator-cli.md#version-20-runtime-parameter-context).
- **SD** - see [Solution Descriptor](/docs/envgene-objects.md#solution-descriptor).
- **SD Merge Mode** - see [SD merge](/docs/features/sd-processing.md#sd-merge).
- **Secret Store** - see [Secret Store](/docs/envgene-objects.md#secret-store).
- **`SECRET_FLOW`** - see [`SECRET_FLOW` attribute](/docs/features/external-creds.md#secret_flow-attribute).
- **Shared Credentials File** - see [Shared Credentials File](/docs/envgene-objects.md#shared-credentials-file).
- **Shared Template Variable File** - see [Shared Template Variable
  Files](/docs/envgene-objects.md#shared-template-variable-files).
- **Solution Descriptor** - see [Solution Descriptor](/docs/envgene-objects.md#solution-descriptor).
- **System Credentials File** - see [System Credentials
  File](/docs/envgene-objects.md#system-credentials-file-in-instance-repository).
- **`technicalConfigurationParameters`** - see [Runtime Parameter
  Context](/docs/features/calculator-cli.md#version-20-runtime-parameter-context).
- **Template Composition** - see [Template Composition](/docs/features/template-composition.md).
- **Template Descriptor** - see [Template Descriptor](/docs/envgene-objects.md#template-descriptor).
- **Template Override** - see [Template Override](/docs/features/template-override.md).
- **Template Pipeline** - see [Template Pipeline Parameters](/docs/template-pipeline-parameters.md).
- **Template Repository** - see [Template Repository Objects](/docs/envgene-objects.md#template-repository-objects).
- **Template Resource Profile Override** - see [Template Resource Profile
  Override](/docs/envgene-objects.md#template-resource-profile-override).
- **Template Variables** - see
  [`current_env.additionalTemplateVariables`](/docs/template-macros.md#current_envadditionaltemplatevariables).
- **Template-rendered Definition** - see [Templates](/docs/features/app-reg-defs.md#templates).
- **Tenant** - see [Tenant](/docs/envgene-objects.md#tenant).
- **Tenant Template** - see [Tenant Template](/docs/envgene-objects.md#tenant-template).
- **Topology Context** - see [Topology Context](/docs/features/calculator-cli.md#version-20-topology-context).
- **VALS** - see [Parameter with VALS reference](/docs/features/external-creds.md#parameter-with-vals-reference).
- **Warmup** - see [Warmup and why it matters](/docs/features/blue-green-deployment.md#warmup-and-why-it-matters).

## Terms with several meanings

### Application

1. **Application object** - parameters of one application in one Namespace. See
   [Application](/docs/envgene-objects.md#application).
2. **Application in the Solution Descriptor** - an `application:version` entry, the unit that is deployed. See [Solution
   Descriptor](/docs/envgene-objects.md#solution-descriptor).
3. **Service** - a component of an application from its SBOM, the per-service scope of the Effective Set. See [Service
   Inclusion Criteria](/docs/features/calculator-cli.md#version-20-service-inclusion-criteria-and-naming-convention).

### Artifact

1. **Environment Template Artifact** - `envTemplate.artifact`. See [Artifact
   Definition](/docs/envgene-objects.md#artifact-definition).
2. **Application artifact** - DD, Helm chart, or Docker image of an application. See [Artifact
   Resolution](/docs/features/artifact-resolution.md).
3. **Job artifact** - `save_artifacts.strategy`, ADR-0002. See [Troubleshooting
   Artifacts](/docs/features/troubleshooting-artifacts.md).
4. **Leftover files on the runner node** - removed at run start, ADR-0008. See
   [preprocess](/docs/technical-design/instance-pipeline/steps/preprocess.md).

### Baseline

1. **Application baseline** - parameter set the application ships in its Helm chart, ADR-0009 (app chart). See
   [Three-level hierarchy](/docs/features/resource-profile.md#three-level-hierarchy).
2. **`baseline` field** - selector in `profile.baseline` and in a Resource Profile Override, ADR-0006. See [Baseline
   resolution](/docs/features/resource-profile.md#baseline-resolution-within-the-active-side).
3. **Composite Structure baseline** - core namespace or BG Domain, unrelated to resource profiles. See [Composite
   Structure](/docs/envgene-objects.md#composite-structure).

### Clean

1. **`CLEAN` operation** - `OPERATION_TYPE: CLEAN`, replaces namespace content with a `.cleaned` marker. See
   [Cleanup](/docs/features/clean.md).
2. **Cleanup context** - Effective Set part for teardown, ADR-0011. See [Cleanup
   Context](/docs/features/calculator-cli.md#version-20-cleanup-context).
3. **Working tree cleanup** - untracked files removed at run start, ADR-0008. See
   [preprocess](/docs/technical-design/instance-pipeline/steps/preprocess.md).

### Context

1. **Effective Set context** - deployment, runtime, pipeline, topology, cleanup, External Credential Context. See
   [Effective Set v2.0](/docs/features/calculator-cli.md#effective-set-v20).
2. **Rendering context** - variables a Jinja template sees, such as `current_env`. See [Template
   Macros](/docs/template-macros.md).

### Definition

1. **Application and Registry Definition** - AppDef and RegDef, rendered, overridden, then effective. See [Application
   and Registry Definition](/docs/features/app-reg-defs.md).
2. **Artifact Definition** - locates the Environment Template Artifact only. See [Artifact
   Definition](/docs/envgene-objects.md#artifact-definition).

### Deployment Descriptor

1. **DD JSON** - component list of an application, ADR-0003, ADR-0012 (SBOM source). See [SBOM
   Generation](/docs/features/sbom-generation.md).
2. **DD ZIP part** - no longer downloaded, ADR-0009 (app chart). See [ADR-0009 (app
   chart)](/docs/adr/0009-download-app-chart-for-sbom-generation.md).
3. **`deployDescriptor` block** - read-only image data in the deployment context, ADR-0005. See
   [ADR-0005](/docs/adr/0005-decompose-custom-params-deployment-overrides.md).

### External

1. **`external` Credential type** - value in a Secret Store, `$type: credRef`. See
   [Credential](/docs/envgene-objects.md#credential).
2. **External mode** - `/configuration/secret-stores.yml` exists, ADR-0009 (shared template). See [Mode
   detection](/docs/features/credential-processing.md#mode-detection).
3. **External systems** - deployers and CMDB outside EnvGene. See [Deployment
   architecture](/docs/deployment-architecture.md).

### Macro

1. **Jinja macro** - resolved during Environment Instance generation, such as `current_env.name`. See [Jinja
   Macros](/docs/template-macros.md#jinja-macros).
2. **Calculator CLI macro** - resolved during Effective Set calculation, such as `NAMESPACE`. See [Calculator
   command-line tool macros](/docs/template-macros.md#calculator-command-line-tool-macros).
3. **Credential macro** - `creds.get` and deprecated `#creds`, rewritten in external mode, ADR-0009 (shared template).
   See [Credential Macro and Credential Reference](/docs/template-macros.md#credential-macro-and-credential-reference).

### Merge mode

1. **SD merge mode** - `SD_REPO_MERGE_MODE`. See [SD merge](/docs/features/sd-processing.md#sd-merge).
2. **Resource profile merge mode** - `inventory.config.mergeEnvSpecificResourceProfiles`, ADR-0006. See [Merge and
   replace](/docs/features/resource-profile.md#merge-and-replace).
3. **Effective Set merge** - forward or reverse merge in partial generation. See [Forward
   merge](/docs/features/effective-set-generation.md#forward-merge) and [Reverse
   merge](/docs/features/effective-set-generation.md#reverse-merge).

### Namespace name

1. **Namespace folder name** - keys `envSpecificResourceProfiles` and Effective Set folders. See [Environment-specific
   Resource Profile Override](/docs/features/resource-profile.md#environment-specific-resource-profile-override).
2. **Namespace `name` attribute** - the Kubernetes namespace name, mapped in `mapping.yaml`. See
   [Namespace](/docs/envgene-objects.md#namespace).
3. **Deploy Postfix** - namespace role in the SD, `useDeployPostfixAsNamespace`. See [`useDeployPostfixAsNamespace`
   Handling](/docs/features/sd-processing.md#usedeploypostfixasnamespace-handling).

### Override

1. **Resource Profile Override** - `profile.name`, `envSpecificResourceProfiles`. "Template override" in ADR-0006 means
   this. See [Resource profiles](/docs/features/resource-profile.md).
2. **Template Override** - `template_override` on a Cloud or Namespace. See [Template
   Override](/docs/features/template-override.md).
3. **Definition Override** - plain AppDef or RegDef file in the Instance repository. See [Definition
   overrides](/docs/features/app-reg-defs.md#definition-overrides).
4. **Custom Params override** - `CUSTOM_PARAMS`, ADR-0005. See
   [`CUSTOM_PARAMS`](/docs/instance-pipeline-parameters.md#custom_params).

### Parameters

1. **Parameter sections** - `deployParameters`, `e2eParameters`, `technicalConfigurationParameters`. See
   [Cloud](/docs/envgene-objects.md#cloud).
2. **ParameterSet** - reusable named container of parameters. See [Template
   ParameterSet](/docs/envgene-objects.md#template-parameterset).
3. **Pipeline parameters** - inputs of a run, such as `ENV_NAMES`. See [Instance Pipeline
   Parameters](/docs/instance-pipeline-parameters.md).

### Pipeline

1. **Instance pipeline** - generates the Environment Instance and Effective Set. See [Instance
   pipeline](/docs/envgene-pipelines.md#instance-pipeline).
2. **Template and Discovery pipelines** - pipelines of the other two repositories. See [Template Pipeline
   Parameters](/docs/template-pipeline-parameters.md).
3. **Pipeline context** - Effective Set part from `e2eParameters`. See [Pipeline Parameter
   Context](/docs/features/calculator-cli.md#version-20-pipeline-parameter-context).
4. **Pipeline type** - `PIPELINE_TYPE`: `LEGACY` or `GITLAB_DEPLOY`. See
   [`PIPELINE_TYPE`](/docs/instance-pipeline-parameters.md#pipeline_type).

### Profile

1. **`profile` attribute** - `name` and `baseline` on a Cloud or Namespace. See [Cloud](/docs/envgene-objects.md#cloud).
2. **Resource Profile as the override object** - `resource-profile.schema.json`, `resource_profiles/` folders. See
   [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override).
3. **Resource Profile as the result** - baseline plus override that a service receives. See [Resource
   profiles](/docs/features/resource-profile.md).
4. **Namespace profile and cloud profile** - only one is used, ADR-0006. See [Side
   selection](/docs/features/resource-profile.md#side-selection).

### Registry

1. **Registry Definition** - RegDef in `/regdefs`. See [Registry
   Definition](/docs/envgene-objects.md#registry-definition).
2. **`registry.yml`** - deprecated config, `--registries` of the Calculator CLI. See
   [`registry.yml`](/docs/envgene-configs.md#registryyml).
3. **Registry provider** - `MAVEN_PROVIDER` value such as `aws`, `gcp`, or `nexus` (ADR-0001), or the provider a RegDef
   v2 declares. See [Artifact Resolution](/docs/features/artifact-resolution.md).

### Repository

1. **Template and Instance Repository** - the two EnvGene Git repositories. See [EnvGene
   Objects](/docs/envgene-objects.md).
2. **Discovery repository** - generates Cloud Passports. See [Discovery Pipeline
   Parameters](/docs/discovery-pipeline-parameters.md).
3. **DCL repository** - No-CMDB v2 push target for Effective Set contexts. See [No-CMDB
   v2](/docs/deployment-architecture.md#no-cmdb-v2).
4. **Group repository** - Helm repository for a rebuilt chart URL, ADR-0009 (app chart). See [SBOM
   Generation](/docs/features/sbom-generation.md).

### SBOM

1. **Application SBOM** - `application.sbom.schema.json`. See [Application
   SBOM](/docs/features/sbom.md#application-sbom).
2. **Environment Template SBOM** - `env-template.sbom.schema.json`. See [Environment Template
   SBOM](/docs/features/sbom.md#environment-template-sbom).
3. **Solution SBOM** - `solution.sbom.schema.json`. See
   [`solution.sbom.schema.json`](/schemas/solution.sbom.schema.json).

### Side

1. **Resource profile active side** - Namespace or Cloud, ADR-0006. See [Side
   selection](/docs/features/resource-profile.md#side-selection).
2. **Blue-Green side** - origin or peer, `BG_NS_TARGET`, role active, idle, candidate, or legacy. See [Lifecycle in
   plain terms](/docs/features/blue-green-deployment.md#lifecycle-in-plain-terms).
3. **Deploy side** - path that pulls charts and images, ADR-0012 (coordinate source), not `inventory.deployer`. See
   [ADR-0012 (coordinate source)](/docs/adr/0012-select-artifact-coordinate-source.md).

### Template

1. **Environment Template** - Template Descriptor plus Tenant, Cloud, and Namespace templates. See [Environment Template
   Objects](/docs/envgene-objects.md#environment-template-objects).
2. **Object templates** - ParameterSet, Resource Profile Override, Credential, AppDef, RegDef templates. See [Template
   Repository Objects](/docs/envgene-objects.md#template-repository-objects).

### Version

1. **RegDef and Artifact Definition v1.0 and v2.0** - schema versions, `version: "2.0"`. See [Registry
   Definition](/docs/envgene-objects.md#registry-definition).
2. **Effective Set v1.0 and v2.0** - `--effective-set-version`. See [Effective Set
   v2.0](/docs/features/calculator-cli.md#effective-set-v20).
3. **No-CMDB v1 and v2** - `inventory.noCmdbVersion`. See [Deployment architecture](/docs/deployment-architecture.md).
4. **Application version** - `version` in `application:version`. See [Solution
   Descriptor](/docs/envgene-objects.md#solution-descriptor).
5. **SD version** - SD schema version, only 2.1 and 2.2 are usable. `SD_VERSION` is a different thing: the SD artifact
   to download. See [Solution Descriptor](/docs/envgene-objects.md#solution-descriptor) and
   [`SD_VERSION`](/docs/instance-pipeline-parameters.md#sd_version).
