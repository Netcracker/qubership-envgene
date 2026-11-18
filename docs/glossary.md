# Glossary

- [Glossary](#glossary)
  - [How to use this glossary](#how-to-use-this-glossary)
  - [Application](#application)
  - [Artifact](#artifact)
  - [Baseline](#baseline)
  - [Clean](#clean)
  - [Context](#context)
  - [Definition](#definition)
  - [Delta](#delta)
  - [Deployment Descriptor](#deployment-descriptor)
  - [External](#external)
  - [Merge Mode](#merge-mode)
  - [Namespace Name](#namespace-name)
  - [Override](#override)
  - [Parameters](#parameters)
  - [Pipeline](#pipeline)
  - [Profile](#profile)
  - [Side](#side)
  - [Template](#template)
  - [Version](#version)

This glossary lists the EnvGene words that have more than one meaning, where picking the wrong meaning changes what a
change touches. Each entry splits the word into its senses, names the field or ADR where each sense appears, and links
to the document that defines it.

## How to use this glossary

A word gets an entry when it appears in the Decision or Consequences section of an ADR under `docs/adr/`, or in the
name of a field, and has more than one sense. Words with one meaning are not listed here. Look them up in
[EnvGene Objects](/docs/envgene-objects.md), [Configuration Files](/docs/envgene-configs.md), and the
[feature docs](/docs/features/).

When you meet a listed word, decide which sense it carries before you act on it.

## Application

1. **Application object.** The EnvGene object in the Environment Instance that holds parameters of one application in
   one Namespace, generated from the `applications` section of ParameterSets. See
   [Application](/docs/envgene-objects.md#application).
2. **Application in the Solution Descriptor.** An `application:version` entry with a `deployPostfix`, the unit that is
   deployed and for which an Application SBOM is generated. See
   [Solution Descriptor](/docs/envgene-objects.md#solution-descriptor).
3. **Service.** A component of an application, taken from its Application SBOM. The Effective Set writes per-service
   parameters, so "per application" and "per service" are different scopes. See [Service Inclusion
   Criteria](/docs/features/calculator-cli.md#version-20-service-inclusion-criteria-and-naming-convention).

## Artifact

1. **Environment Template Artifact.** The versioned Maven artifact with the Environment Templates, set in
   `envTemplate.artifact`. Its location is described by an Artifact Definition. See
   [Artifact Definition](/docs/envgene-objects.md#artifact-definition).
2. **Application artifact.** An artifact of an application, such as its Deployment Descriptor, Helm chart, or Docker
   image. Its location is described by an Application Definition and a Registry Definition. See
   [Artifact Resolution](/docs/features/artifact-resolution.md).
3. **Job artifact.** The files a pipeline job saves for troubleshooting, decided by `save_artifacts.strategy`
   (ADR-0002). See [Troubleshooting Artifacts](/docs/features/troubleshooting-artifacts.md).

## Baseline

1. **Application baseline.** A named set of performance parameters, such as `dev` or `prod`, that an application ships
   for its services in its Helm chart. The configurator cannot change its values, only select it. See
   [Three-level hierarchy](/docs/features/resource-profile.md#three-level-hierarchy).
2. **`baseline` field.** The name that selects one application baseline. It is set in `profile.baseline` on a Cloud or
   Namespace and in the `baseline` field of a Resource Profile Override. Precedence among these fields is set by
   ADR-0006. See
   [Baseline resolution](/docs/features/resource-profile.md#baseline-resolution-within-the-active-side).
3. **Composite Structure baseline.** The core namespace, or BG Domain, that the satellite namespaces of a solution
   depend on. It is unrelated to resource profiles. See [Composite
   Structure](/docs/envgene-objects.md#composite-structure).

## Clean

1. **`CLEAN` operation.** An Instance pipeline run with `OPERATION_TYPE: CLEAN`, available only in No-CMDB v2. It
   replaces the content of the target namespaces with a `.cleaned` marker. See [Cleanup](/docs/features/clean.md).
2. **Cleanup context.** The part of the Effective Set with per-namespace parameters for teardown. Only No-CMDB v1
   generates it, on every deploy (ADR-0011). See
   [Cleanup Context](/docs/features/calculator-cli.md#version-20-cleanup-context).
3. **Working tree cleanup.** Removing untracked files from the runner's checkout at the start of each run (ADR-0008).
   It is unrelated to cleaning a namespace. See
   [preprocess](/docs/technical-design/instance-pipeline/steps/preprocess.md).

## Context

1. **Effective Set context.** One of the parts of the Effective Set, each for its own consumer: deployment, runtime,
   pipeline, topology, cleanup, and External Credential Context. See
   [Effective Set v2.0](/docs/features/calculator-cli.md#effective-set-v20).
2. **Rendering context.** The variables a Jinja template sees during Environment Instance generation, such as
   `current_env`. See [Template Macros](/docs/template-macros.md).

## Definition

1. **Application Definition and Registry Definition.** Also called AppDef and RegDef. They map `application:version`
   to registry and Maven coordinates of an application artifact. See
   [Application and Registry Definition](/docs/features/app-reg-defs.md).
2. **Artifact Definition.** The same mapping for the Environment Template Artifact only. See
   [Artifact Definition](/docs/envgene-objects.md#artifact-definition).
3. **Template-rendered, Definition Override, and Effective Definition.** The stages of an AppDef or RegDef: rendered
   from a template, replaced by a plain file in the Instance repository, and the final result in `/appdefs/` and
   `/regdefs/`. See [Definition overrides](/docs/features/app-reg-defs.md#definition-overrides).

## Delta

1. **Delta SD.** The incoming Solution Descriptor changes, passed between steps of one run and never committed. It
   drives partial Effective Set generation in the SD flow. See [Delta SD](/docs/features/sd-processing.md#delta-sd).
2. **Delta deploy plan.** The `delta-deploy-plan.yml` with the deployments of the current operation. For
   `PIPELINE_TYPE: GITLAB_DEPLOY` it is what the Calculator CLI receives through `--deploy-plan-path`. See
   [Calculator CLI attributes](/docs/features/calculator-cli.md#calculator-command-line-tool-execution-attributes).

## Deployment Descriptor

1. **Deployment Descriptor JSON.** Also called DD. The record of the deployable components of an application. The
   Application SBOM takes its component list from it only (ADR-0003, ADR-0012). See
   [SBOM Generation](/docs/features/sbom-generation.md).
2. **DD ZIP part.** The archive delivered with the DD. EnvGene no longer downloads it. The resource-profile baselines
   are read from the application Helm chart instead (ADR-0009). See
   [ADR-0009](/docs/adr/0009-download-app-chart-for-sbom-generation.md).

## External

1. **`external` Credential type.** A Credential whose value lives in a Secret Store, referenced by `$type: credRef`.
   See [Credential](/docs/envgene-objects.md#credential).
2. **External mode.** A repository-wide state of the Instance repository, on when `/configuration/secret-stores.yml`
   exists. In external mode, `creds.get` is rewritten to Credential References (ADR-0009). See
   [Mode detection](/docs/features/credential-processing.md#mode-detection).
3. **External systems.** Tools outside EnvGene that consume its output, such as deployers and CMDB.

## Merge Mode

1. **SD merge mode.** How an incoming Solution Descriptor is combined with the Full SD, set by `SD_REPO_MERGE_MODE`:
   `basic-merge` (the default), `basic-exclusion-merge`, or `replace`. See
   [SD merge](/docs/features/sd-processing.md#sd-merge).
2. **Resource profile merge mode.** Whether the environment-specific Resource Profile Override merges with or replaces
   the template override, set by `inventory.config.mergeEnvSpecificResourceProfiles`. Changing a baseline needs
   replace mode (ADR-0006). See [Merge and replace](/docs/features/resource-profile.md#merge-and-replace).
3. **Effective Set merge.** How partial generation writes into the existing Effective Set: forward merge for
   `basic-merge`, reverse merge for `basic-exclusion-merge`. See
   [Partial Generation](/docs/features/effective-set-generation.md#partial-generation).

## Namespace Name

1. **Namespace folder name.** The folder under `Namespaces/` in the Environment Instance. It keys
   `envTemplate.envSpecificResourceProfiles` and the Effective Set folders, and usually matches the Deploy Postfix.
2. **Namespace `name` attribute.** The real Kubernetes namespace name. The Effective Set maps folders to these names in
   `mapping.yaml`. See [Namespace](/docs/envgene-objects.md#namespace).
3. **Deploy Postfix.** The namespace role used in the Solution Descriptor. With
   `useDeployPostfixAsNamespace: true` the SD carries the `name` attribute instead, and EnvGene converts it. See
   [`useDeployPostfixAsNamespace` Handling](/docs/features/sd-processing.md#usedeploypostfixasnamespace-handling).

## Override

1. **Resource Profile Override.** Custom performance values on top of a baseline. Template overrides come from
   `profile.name`, environment-specific overrides from `envTemplate.envSpecificResourceProfiles`, and the combined
   result lives in the Environment Instance. See [Resource profiles](/docs/features/resource-profile.md).
2. **Template Override.** The `template_override` attribute that merges content into a rendered Cloud or Namespace. See
   [Template Override](/docs/features/template-override.md).
3. **Definition Override.** A plain AppDef or RegDef file in the Instance repository that replaces the rendered one.
   See [Definition overrides](/docs/features/app-reg-defs.md#definition-overrides).
4. **Custom Params override.** Session parameters from `CUSTOM_PARAMS`, applied to the deployment and runtime contexts
   with the highest priority (ADR-0005). See [`CUSTOM_PARAMS`](/docs/instance-pipeline-parameters.md#custom_params).

## Parameters

1. **Parameter sections.** `deployParameters`, `e2eParameters`, and `technicalConfigurationParameters` on Tenant,
   Cloud, Namespace, and Application. They feed the deployment, pipeline, and runtime contexts. See
   [Cloud](/docs/envgene-objects.md#cloud).
2. **ParameterSet.** A reusable named container of parameters, referenced from a template or the Environment Inventory.
   See [Template ParameterSet](/docs/envgene-objects.md#template-parameterset).
3. **Pipeline parameters.** Inputs of a pipeline run, such as `ENV_NAMES` or `SD_DATA`. See
   [Instance Pipeline Parameters](/docs/instance-pipeline-parameters.md).

## Pipeline

1. **Instance pipeline.** The pipeline in the Instance repository that generates the Environment Instance and the
   Effective Set. See [Instance pipeline](/docs/envgene-pipelines.md#instance-pipeline).
2. **Template pipeline and Discovery pipeline.** The pipelines of the Template and Discovery repositories. See
   [Template Pipeline Parameters](/docs/template-pipeline-parameters.md) and
   [Discovery Pipeline Parameters](/docs/discovery-pipeline-parameters.md).
3. **Pipeline context.** The part of the Effective Set built from `e2eParameters` for orchestrators. See
   [Pipeline Parameter Context](/docs/features/calculator-cli.md#version-20-pipeline-parameter-context).
4. **Pipeline type.** `PIPELINE_TYPE`, `LEGACY` (the default) or `GITLAB_DEPLOY`. Many parameters and the `CLEAN` and
   `BGD` operations apply only to `GITLAB_DEPLOY`. See
   [`PIPELINE_TYPE`](/docs/instance-pipeline-parameters.md#pipeline_type).

## Profile

1. **`profile` attribute.** The object on a Cloud or Namespace with `name`, the Resource Profile Override to apply,
   and `baseline`. See [Cloud](/docs/envgene-objects.md#cloud).
2. **Resource Profile.** The result for a service: the application baseline plus the override on top. See
   [Resource profiles](/docs/features/resource-profile.md).
3. **Namespace profile and cloud profile.** The `profile` of one of the two objects. Only one of them is used, chosen
   by side selection (ADR-0006). See [Side selection](/docs/features/resource-profile.md#side-selection).

## Side

1. **Resource profile side.** The Namespace or the Cloud, whichever EnvGene takes the resource profile from. The
   Namespace wins when it has its own baseline or an override (ADR-0006). See
   [Side selection](/docs/features/resource-profile.md#side-selection).
2. **Blue-Green side.** The origin or peer namespace of a BG Domain, selected by `BG_NS_TARGET`. Its role is active,
   idle, candidate, or legacy. See [Lifecycle in plain
   terms](/docs/features/blue-green-deployment.md#lifecycle-in-plain-terms).
3. **Deploy side.** The deployer outside EnvGene that pulls charts and images. ADR-0009 and ADR-0012 require EnvGene
   to resolve the same chart as the deploy side. See
   [ADR-0012](/docs/adr/0012-select-artifact-coordinate-source.md).

## Template

1. **Environment Template.** The Template Descriptor plus the Tenant, Cloud, and Namespace templates for one solution
   type. See [Environment Template Objects](/docs/envgene-objects.md#environment-template-objects).
2. **Object templates.** Jinja files for other objects: ParameterSets, Template Resource Profile Overrides, Credential
   Templates, and AppDef and RegDef templates. See
   [Template Repository Objects](/docs/envgene-objects.md#template-repository-objects).
3. **Template Override and Template Composition.** Ways to reuse templates: merging content into a rendered object, or
   building a child template from parent templates. See [Template Override](/docs/features/template-override.md) and
   [Template Composition](/docs/features/template-composition.md).

## Version

1. **RegDef and Artifact Definition v1.0 and v2.0.** Object schema versions. v2.0 sets `version: "2.0"` and supports
   cloud registry authentication. See [Registry Definition](/docs/envgene-objects.md#registry-definition).
2. **Effective Set v1.0 and v2.0.** The output layout, set by `--effective-set-version`. See
   [Effective Set v2.0](/docs/features/calculator-cli.md#effective-set-v20).
3. **No-CMDB v1 and v2.** Deployment architectures, set by `inventory.noCmdbVersion`. See
   [Deployment architecture](/docs/deployment-architecture.md).
4. **Application version.** The `version` part of `application:version` in the Solution Descriptor.
