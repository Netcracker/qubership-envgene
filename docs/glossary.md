# Glossary

- [Glossary](#glossary)
  - [Active Side](#active-side)
  - [Application](#application)
  - [Application Definition](#application-definition)
  - [Application SBOM](#application-sbom)
  - [Artifact Definition](#artifact-definition)
  - [Baseline](#baseline)
  - [BG Domain](#bg-domain)
  - [BG State Files](#bg-state-files)
  - [Blue-Green Deployment](#blue-green-deployment)
  - [Calculator CLI](#calculator-cli)
  - [Cleanup Context](#cleanup-context)
  - [Cloud](#cloud)
  - [Cloud Passport](#cloud-passport)
  - [Composite Structure](#composite-structure)
  - [Credential](#credential)
  - [Credential Reference](#credential-reference)
  - [Credential Template](#credential-template)
  - [Custom Params](#custom-params)
  - [Definition Override](#definition-override)
  - [Delta SD](#delta-sd)
  - [Deploy Postfix](#deploy-postfix)
  - [Deployment Architecture](#deployment-architecture)
  - [Deployment Descriptor](#deployment-descriptor)
  - [Deployment Parameter Context](#deployment-parameter-context)
  - [Effective Definition](#effective-definition)
  - [Effective Set](#effective-set)
  - [Environment](#environment)
  - [Environment Credentials File](#environment-credentials-file)
  - [Environment Instance](#environment-instance)
  - [Environment Inventory](#environment-inventory)
  - [Environment Specific ParameterSet](#environment-specific-parameterset)
  - [Environment Specific Resource Profile Override](#environment-specific-resource-profile-override)
  - [Environment Template](#environment-template)
  - [Environment Template Artifact](#environment-template-artifact)
  - [Environment Template SBOM](#environment-template-sbom)
  - [ESO](#eso)
  - [External Credential Context](#external-credential-context)
  - [Full SD](#full-sd)
  - [Instance Pipeline](#instance-pipeline)
  - [Instance Repository](#instance-repository)
  - [Macro](#macro)
  - [Namespace](#namespace)
  - [ParameterSet](#parameterset)
  - [Pipeline Parameter Context](#pipeline-parameter-context)
  - [Registry Definition](#registry-definition)
  - [Resource Profile](#resource-profile)
  - [Resource Profile Override](#resource-profile-override)
  - [Runtime Parameter Context](#runtime-parameter-context)
  - [SBOM](#sbom)
  - [SD Merge Mode](#sd-merge-mode)
  - [Secret Store](#secret-store)
  - [Shared Credentials File](#shared-credentials-file)
  - [Shared Template Variable File](#shared-template-variable-file)
  - [Solution Descriptor](#solution-descriptor)
  - [System Credentials File](#system-credentials-file)
  - [Template Composition](#template-composition)
  - [Template Descriptor](#template-descriptor)
  - [Template Override](#template-override)
  - [Template Pipeline](#template-pipeline)
  - [Template Repository](#template-repository)
  - [Template Resource Profile Override](#template-resource-profile-override)
  - [Template-rendered Definition](#template-rendered-definition)
  - [Tenant](#tenant)
  - [Topology Context](#topology-context)
  - [VALS](#vals)
  - [Warmup](#warmup)

This glossary provides definitions of key terms used in the EnvGene documentation.

## Active Side

The object, a [Namespace](#namespace) or a [Cloud](#cloud), whose profile EnvGene uses to resolve the
[Resource Profile](#resource-profile) of an application. The Namespace is the active side when its own profile
carries any signal, meaning its `profile.baseline` is set or a [Resource Profile Override](#resource-profile-override)
is present for it. Otherwise the cloud profile is used as a fallback. See
[Side selection](/docs/features/resource-profile.md#side-selection).

## Application

An EnvGene object that holds parameters specific to one application within a [Namespace](#namespace). Generated
from the `applications` section of [ParameterSets](#parameterset). See
[Application](/docs/envgene-objects.md#application).

## Application Definition

An object that maps an application name to its artifact ID, group ID, and [Registry Definition](#registry-definition),
so that the `application:version` notation resolves to a downloadable Maven artifact. See
[Application Definition](/docs/envgene-objects.md#application-definition).

## Application SBOM

A CycloneDX JSON file describing an application: its services, the coordinates of their artifacts, and their
attributes, including [Baselines](#baseline). The [Calculator CLI](#calculator-cli) reads it to build the
[Effective Set](#effective-set). See [SBOM types](/docs/features/sbom.md#application-sbom).

## Artifact Definition

An object that describes where the [Environment Template Artifact](#environment-template-artifact) is stored, so that
its `application:version` notation resolves to a registry and Maven coordinates. See
[Artifact Definition](/docs/envgene-objects.md#artifact-definition).

## Baseline

A named set of performance parameters, such as CPU, memory, and replicas, that an application ships for its services.
Typical names are `dev` and `prod`, but the name is free-form. A configurator selects a baseline and cannot change its
values except through a [Resource Profile Override](#resource-profile-override). See
[Three-level hierarchy](/docs/features/resource-profile.md#three-level-hierarchy).

## BG Domain

An EnvGene object that groups the three namespaces of a [Blue-Green Deployment](#blue-green-deployment): origin and
peer, which hold the two application sides, and controller, which hosts the coordination service. See
[BG Domain](/docs/envgene-objects.md#bg-domain).

## BG State Files

Empty marker files in the environment folder, such as `.origin-active` or `.peer-idle`, that record the current state
of the origin and peer sides of a [BG Domain](#bg-domain). See
[What state files tell you](/docs/features/blue-green-deployment.md#what-state-files-tell-you).

## Blue-Green Deployment

A release pattern, also called BGD, that keeps two copies of the same application stack side by side, one serving
live traffic and one being prepared for promotion. In EnvGene it is modeled by a [BG Domain](#bg-domain) and requires
the No-CMDB v2 [Deployment Architecture](#deployment-architecture). See
[Blue-Green Deployment](/docs/features/blue-green-deployment.md).

## Calculator CLI

The command-line tool, also called the Effective Set generator, that computes the [Effective Set](#effective-set) from
the [Environment Instance](#environment-instance), the [Solution Descriptor](#solution-descriptor), and the
[Application SBOMs](#application-sbom). See [Calculator CLI](/docs/features/calculator-cli.md).

## Cleanup Context

The part of the [Effective Set](#effective-set) that holds per-namespace parameters and credentials for removing a
namespace from a cluster. EnvGene does not remove anything itself. Teardown tooling consumes this context. See
[Cleanup](/docs/features/clean.md).

## Cloud

An EnvGene object that holds cluster-level parameters, common to all namespaces of the
[Environment](#environment). Rendered from the Cloud template. See [Cloud](/docs/envgene-objects.md#cloud).

## Cloud Passport

A contracted set of parameters describing a cluster and the platform applications installed in it, such as databases
and message brokers. It is obtained through cloud discovery or gathered manually, and merged into the [Cloud](#cloud)
object during [Environment Instance](#environment-instance) generation. See
[Cloud Passport](/docs/envgene-objects.md#cloud-passport).

## Composite Structure

An EnvGene object that describes how a solution is composed: a baseline, which is the core infrastructure namespace
or a [BG Domain](#bg-domain), and the satellite namespaces that consume its services. This baseline is unrelated to
the Resource Profile [Baseline](#baseline). See [Composite Structure](/docs/envgene-objects.md#composite-structure).

## Credential

An EnvGene object that holds a sensitive parameter. Its `type` is `usernamePassword` or `secret` for a value kept
encrypted in the repository, or `external` for a value kept in a [Secret Store](#secret-store). See
[Credential](/docs/envgene-objects.md#credential).

## Credential Reference

A parameter value of `$type: credRef` that points at an `external` [Credential](#credential) by its `credId`. The
local counterpart is the `creds.get` [Macro](#macro). See
[Credential Reference](/docs/features/external-creds.md#credential-reference).

## Credential Template

A Jinja file in the [Template Repository](#template-repository) that renders `external` [Credentials](#credential).
See [Credential Template](/docs/envgene-objects.md#credential-template).

## Custom Params

Session-scoped parameters passed via the Instance pipeline parameter [`CUSTOM_PARAMS`](/docs/instance-pipeline-parameters.md#custom_params) and applied to the [Effective Set](/docs/features/calculator-cli.md#version-20-effective-set-structure) with the highest priority. Custom Params are not persisted between parameter calculation sessions and are treated as sensitive. See [Calculator CLI](/docs/features/calculator-cli.md) for details.

## Definition Override

A plain YAML file in the instance repository that replaces a Template-rendered Definition with the same filename, or adds a new definition. Applied as-is, never rendered. See [Definition overrides](/docs/features/app-reg-defs.md#definition-overrides).

## Delta SD

A partial [Solution Descriptor](#solution-descriptor) with incremental changes to apply to the [Full SD](#full-sd).
It exists only within one pipeline run and drives partial [Effective Set](#effective-set) generation. See
[Delta SD](/docs/features/sd-processing.md#delta-sd).

## Deploy Postfix

A short identifier for a [Namespace](/docs/envgene-objects.md#namespace) role. Used in the Solution Descriptor. Typically matches the namespace folder name or template name.

## Deployment Architecture

The way EnvGene delivers its output for an [Environment](#environment), one of CMDB, No-CMDB v1, or No-CMDB v2. CMDB
imports the [Environment Instance](#environment-instance) into an external CMDB. No-CMDB v1 commits the
[Effective Set](#effective-set) to the [Instance Repository](#instance-repository). No-CMDB v2 also splits the
Effective Set by context and pushes part of it to a separate repository. See
[Deployment architecture](/docs/deployment-architecture.md).

## Deployment Descriptor

An application artifact, also called DD, that lists the services of an application and their artifacts. EnvGene
downloads it to generate the [Application SBOM](#application-sbom). See
[SBOM Generation](/docs/features/sbom-generation.md).

## Deployment Parameter Context

The part of the [Effective Set](#effective-set) used to render Helm manifests on application deployment. It merges
the `deployParameters` of the [Tenant](#tenant), [Cloud](#cloud), [Namespace](#namespace), and
[Application](#application) objects with parameters from the [Application SBOM](#application-sbom) and the
[Resource Profile](#resource-profile). See
[Deployment Parameter Context](/docs/features/calculator-cli.md#version-20-deployment-parameter-context).

## Effective Definition

An Application or Registry Definition after template rendering and Definition Overrides are applied. Lives in the root-level `/appdefs/` and `/regdefs/` folders. See [Output layout](/docs/features/app-reg-defs.md#output-layout).

## Effective Set

The complete set of parameters generated for a specific Environment, used by consumers (e.g., ArgoCD). See [Effective Set Structure](/docs/features/calculator-cli.md#version-20-effective-set-structure).

## Environment

A logical grouping representing parameters for deployment target, defined by a unique combination of cluster and environment name (e.g., `cluster-01/env-1`). See [Environment Instance Objects](/docs/envgene-objects.md#environment-instance-objects)

## Environment Credentials File

The file that stores every [Credential](#credential) of an [Environment](#environment), at
`/environments/<cluster-name>/<environment-name>/Credentials/credentials.yml`. See
[Environment Credentials File](/docs/envgene-objects.md#environment-credentials-file).

## Environment Instance

A file structure in the [Instance Repository](#instance-repository) that describes the configuration of one
[Environment](#environment). EnvGene generates it by rendering the [Environment Template](#environment-template) with
the environment-specific parameters from the [Environment Inventory](#environment-inventory). See
[Environment Instance Objects](/docs/envgene-objects.md#environment-instance-objects).

## Environment Inventory

The configuration file describing a specific Environment, including template reference and parameters. See [env_definition.yml](/docs/envgene-configs.md#env_definitionyml).

## Environment Specific ParameterSet

A [ParameterSet](#parameterset) in the [Instance Repository](#instance-repository) that overrides template-level
parameters for one environment or a group of environments. Its values take precedence over Template ParameterSets.
See [Environment Specific ParameterSet](/docs/envgene-objects.md#environment-specific-parameterset).

## Environment Specific Resource Profile Override

A [Resource Profile Override](#resource-profile-override) in the [Instance Repository](#instance-repository) that sets
custom values for one environment, on top of the
[Template Resource Profile Override](#template-resource-profile-override). It wins on conflicts. See
[Environment Specific Resource Profile Override](/docs/envgene-objects.md#environment-specific-resource-profile-override).

## Environment Template

A file structure within the Template Repository describing the structure and parameters of a solution type. Consists of a Template Descriptor and component templates (Tenant, Cloud, Namespaces). Template Descriptors can be Jinja templates (`.yml.j2`, `.yaml.j2`) or static YAML files (`.yml`, `.yaml`).

A single Environment Template can be used for multiple projects or environment types (commonly referred to as a "unified Environment Template"), with namespace filtering used to include only relevant components for each specific deployment. See [Environment Template Objects](/docs/envgene-objects.md#environment-template-objects) and [Namespace Filtering in Template Descriptor](/docs/features/namespace-filtering-in-template-descriptor.md).

## Environment Template Artifact

A versioned Maven artifact containing one or more [Environment Templates](#environment-template) from the Template Repository. Published during Template Repository build process and referenced in the [Environment Inventory](/docs/envgene-configs.md#env_definitionyml) using `application:version` notation (e.g., `project-env-template:v1.2.3`). Used by EnvGene to generate Environment Instances. Also referred to as "Environment Template Artifact". See [Environment Template Objects](/docs/envgene-objects.md#environment-template-objects).

## Environment Template SBOM

A CycloneDX JSON file with the coordinates of an [Environment Template Artifact](#environment-template-artifact). See
[SBOM types](/docs/features/sbom.md#environment-template-sbom).

## ESO

External Secrets Operator, one of two ways an application receives an `external` [Credential](#credential). The
[Effective Set](#effective-set) carries an ESO reference that the operator resolves in the cluster. The alternative is
[VALS](#vals). See [External Credentials Management](/docs/features/external-creds.md#overview).

## External Credential Context

The part of the [Effective Set](#effective-set) with one entry for every `external` [Credential](#credential). Tooling
outside EnvGene reads it to provision secrets in a [Secret Store](#secret-store). See
[External Credential Context](/docs/features/calculator-cli.md#version-20-external-credential-context).

## Full SD

The [Solution Descriptor](#solution-descriptor) that defines the complete application composition of an
[Environment](#environment). There is one per environment, at
`/environments/<cluster-name>/<env-name>/Inventory/solution-descriptor/sd.yml`. See
[Full SD](/docs/features/sd-processing.md#full-sd).

## Instance Pipeline

The main EnvGene pipeline in the [Instance Repository](#instance-repository). It generates the
[Environment Instance](#environment-instance) and the [Effective Set](#effective-set) and, for deploy operations,
hands the result to the deployer. See [Instance pipeline](/docs/envgene-pipelines.md#instance-pipeline).

## Instance Repository

The Git repository containing Environment Inventories, generated Environment Instances, and related configuration.

## Macro

A variable or function available in templates, such as `current_env.name` or `creds.get`. Jinja macros resolve during
[Environment Instance](#environment-instance) generation. Calculator macros resolve during
[Effective Set](#effective-set) calculation. See [Template Macros](/docs/template-macros.md).

## Namespace

An EnvGene object that groups parameters specific to applications within a single namespace in a cluster. Defined in the Environment Instance. See [Namespace](/docs/envgene-objects.md#namespace)

## ParameterSet

A reusable container of parameters that a [Cloud](#cloud) or [Namespace](#namespace) template references by name.
During [Environment Instance](#environment-instance) generation its parameters are set on the referencing object, and
its `applications` section produces [Application](#application) objects. See
[Template ParameterSet](/docs/envgene-objects.md#template-parameterset).

## Pipeline Parameter Context

The part of the [Effective Set](#effective-set) for deployment orchestrators and CI/CD workflows. It is built from the
`e2eParameters` of the [Cloud](#cloud). See
[Pipeline Parameter Context](/docs/features/calculator-cli.md#version-20-pipeline-parameter-context).

## Registry Definition

An object that describes a registry where application artifacts are stored. An
[Application Definition](#application-definition) points to it. See
[Registry Definition](/docs/envgene-objects.md#registry-definition).

## Resource Profile

The performance parameters of a service, such as CPU, memory, and replicas, kept separate from other deployment
parameters. A Resource Profile is a [Baseline](#baseline) plus a [Resource Profile Override](#resource-profile-override)
on top of it. See [Resource profiles](/docs/features/resource-profile.md).

## Resource Profile Override

A set of custom performance values on top of a [Baseline](#baseline), attached to a [Cloud](#cloud) or
[Namespace](#namespace) in the [Environment Instance](#environment-instance). It combines the
[Template Resource Profile Override](#template-resource-profile-override) and the
[Environment Specific Resource Profile Override](#environment-specific-resource-profile-override), and always takes
precedence over the Baseline. See [Resource Profile Override](/docs/envgene-objects.md#resource-profile-override).

## Runtime Parameter Context

The part of the [Effective Set](#effective-set) with parameters that change application behavior without
redeployment. It merges the `technicalConfigurationParameters` of the [Tenant](#tenant), [Cloud](#cloud),
[Namespace](#namespace), and [Application](#application) objects. See
[Runtime Parameter Context](/docs/features/calculator-cli.md#version-20-runtime-parameter-context).

## SBOM

A CycloneDX-based software bill of materials that EnvGene uses to exchange artifact and parameter data. EnvGene uses
two kinds, the [Application SBOM](#application-sbom) and the [Environment Template SBOM](#environment-template-sbom).
See [SBOM](/docs/features/sbom.md).

## SD Merge Mode

The way an incoming [Solution Descriptor](#solution-descriptor) is combined with the [Full SD](#full-sd) already in
the repository, set by `SD_REPO_MERGE_MODE`: `basic-merge`, `basic-exclusion-merge`, `extended-merge`, or `replace`.
See [SD merge](/docs/features/sd-processing.md#sd-merge).

## Secret Store

A named entry in the [Instance Repository](#instance-repository) configuration that describes how to reach an
external secret backend, such as Vault. `external` [Credentials](#credential) point to it. See
[Secret Store](/docs/envgene-objects.md#secret-store).

## Shared Credentials File

A file with [Credentials](#credential) shared across environments. EnvGene copies the relevant ones into the
[Environment Credentials File](#environment-credentials-file) during generation. See
[Shared Credentials File](/docs/envgene-objects.md#shared-credentials-file).

## Shared Template Variable File

A file with template variables shared across environments. EnvGene merges them with `additionalTemplateVariables`
from the [Environment Inventory](#environment-inventory). See
[Shared Template Variable Files](/docs/envgene-objects.md#shared-template-variable-files).

## Solution Descriptor

The object, also called SD, that lists the applications of a solution, each as `application:version` with a
[Deploy Postfix](#deploy-postfix). It is the primary input for [Effective Set](#effective-set) calculation. See
[Solution Descriptor](/docs/envgene-objects.md#solution-descriptor).

## System Credentials File

A file with the [Credentials](#credential) EnvGene itself uses to reach external systems, such as artifact
registries, GitLab, and GitHub. See
[System Credentials File](/docs/envgene-objects.md#system-credentials-file-in-instance-repository).

## Template Composition

A feature that builds a child [Environment Template](#environment-template) from the Tenant, Cloud, and Namespace
templates of one or more parent templates. See [Template Composition](/docs/features/template-composition.md).

## Template Descriptor

The file that describes the structure of an [Environment Template](#environment-template) and links to its Tenant,
Cloud, and Namespace templates. Its filename is the name of the Environment Template. See
[Template Descriptor](/docs/envgene-objects.md#template-descriptor).

## Template Override

A feature that merges the content of the `template_override` attribute into a rendered [Cloud](#cloud) or
[Namespace](#namespace), so one [Environment Template](#environment-template) serves several environment types. See
[Template Override](/docs/features/template-override.md).

## Template Pipeline

The pipeline of the [Template Repository](#template-repository). It runs on every push or merge request, builds the
[Environment Template Artifact](#environment-template-artifact), and publishes it. See
[Template Pipeline Parameters](/docs/template-pipeline-parameters.md).

## Template Repository

The Git repository that holds [Environment Templates](#environment-template), [ParameterSets](#parameterset), Resource
Profile Overrides, and Application and Registry Definition templates. See
[Template Repository Objects](/docs/envgene-objects.md#template-repository-objects).

## Template Resource Profile Override

A [Resource Profile Override](#resource-profile-override) in the [Template Repository](#template-repository) that
applies the same adjustment to all environments of one type. A [Cloud](#cloud) or [Namespace](#namespace) template
references it by `profile.name`. See
[Template Resource Profile Override](/docs/envgene-objects.md#template-resource-profile-override).

## Template-rendered Definition

An Application or Registry Definition produced by rendering a template from the template repository. The filename comes from the definition's `name` field. See [Templates](/docs/features/app-reg-defs.md#templates).

## Tenant

An EnvGene object that holds tenant-level parameters, such as registry configuration and ownership, common to all
environments of the tenant. See [Tenant](/docs/envgene-objects.md#tenant).

## Topology Context

The part of the [Effective Set](#effective-set) that describes how systems and their components relate: the
[Composite Structure](#composite-structure), the [BG Domain](#bg-domain), cluster endpoints, and namespaces. See
[Topology Context](/docs/features/calculator-cli.md#version-20-topology-context).

## VALS

One of two ways an application receives an `external` [Credential](#credential). The [Effective Set](#effective-set)
carries a VALS reference that is resolved into the Helm values at deployment. The alternative is [ESO](#eso). See
[External Credentials Management](/docs/features/external-creds.md#overview).

## Warmup

The [Blue-Green Deployment](#blue-green-deployment) lifecycle step that makes the candidate side a copy of the active
side in Git, so a new version is deployed on top of what production runs. See
[Warmup and why it matters](/docs/features/blue-green-deployment.md#warmup-and-why-it-matters).
